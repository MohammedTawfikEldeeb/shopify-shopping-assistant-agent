import json
from functools import partial

from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langsmith import traceable
from pydantic import BaseModel, Field

from src.infrastructure.llm import make_langchain_llm
from src.prompts import SYSTEM_PROMPT, SUMMARIZE_PROMPT, SUMMARIZE_EXTEND_PROMPT, DB_SCHEMA
from src.agent.states import AgentState
from src.agent.tools import ProductRetriever, SQLQueryTool


class ProductRetrieverInput(BaseModel):
    query: str = Field(description="Concise semantic search query for finding products")


class SQLQueryInput(BaseModel):
    query: str = Field(description="PostgreSQL SELECT query for product details")


product_retriever_tool = StructuredTool.from_function(
    func=lambda query: "",
    name="product_retriever",
    description="Search for products using semantic search. Use ONLY when the user wants to find NEW products. Provide a concise semantic search query.",
    args_schema=ProductRetrieverInput,
)

sql_query_tool = StructuredTool.from_function(
    func=lambda query: "",
    name="sql_query",
    description="Execute a PostgreSQL SELECT query on the product database. Use when the user asks about details of products already found above (options, sizes, colors, prices, variants, images, materials). Write a PostgreSQL SELECT query.",
    args_schema=SQLQueryInput,
)

TOOLS = [product_retriever_tool, sql_query_tool]


def _build_context(summary: str, products: list[dict]) -> str:
    parts = []
    if summary:
        parts.append(f"Previous conversation summary: {summary}")

    if products:
        lines = ["Previously found products:"]
        for p in products:
            extra = []
            if p.get("price"):
                extra.append(f"Price: ${p['price']}")
            if p.get("link"):
                extra.append(f"Link: {p['link']}")
            if p.get("available_sizes"):
                extra.append(f"Sizes: {', '.join(p['available_sizes'])}")
            if p.get("available_colors"):
                extra.append(f"Colors: {', '.join(p['available_colors'])}")
            line = f"- {p['title']} (ID: {p['id']}"
            if extra:
                line += f", {', '.join(extra)}"
            line += ")"
            lines.append(line)
        parts.append("\n".join(lines))
    else:
        parts.append("No products have been found yet.")

    return "\n\n".join(parts)


@traceable(name="agent_node", run_type="chain", tags=["agent", "hakeem"])
async def agent_node(state: AgentState) -> dict:
    llm = make_langchain_llm()
    summary = state.get("summary", "")
    products = state.get("products", [])

    context = _build_context(summary, products)
    system_prompt = SYSTEM_PROMPT.prompt.format(context=context, db_schema=DB_SCHEMA)
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    llm_with_tools = llm.bind_tools(TOOLS)
    response = await llm_with_tools.ainvoke(messages)

    return {"messages": [response]}


@traceable(name="summarize_node", run_type="chain", tags=["summarize", "hakeem"])
async def summarize_node(state: AgentState) -> dict:
    llm = make_langchain_llm()
    summary = state.get("summary", "")

    if summary:
        prompt_text = SUMMARIZE_EXTEND_PROMPT.prompt.format(summary=summary)
    else:
        prompt_text = SUMMARIZE_PROMPT.prompt

    messages = state["messages"]
    summarize_messages = messages + [HumanMessage(content=prompt_text)]
    response = await llm.ainvoke(summarize_messages)

    delete_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]

    return {
        "summary": response.content,
        "messages": delete_messages,
    }


@traceable(name="tools_node", run_type="chain", tags=["tools", "hakeem"])
async def tools_node(
    state: AgentState,
    retriever: ProductRetriever,
    sql_tool: SQLQueryTool,
) -> dict:
    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls

    results = []
    products = state.get("products", [])
    product_ids = state.get("product_ids", [])

    for tool_call in tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"]

        if name == "product_retriever":
            query = args.get("query", "")
            found_products = await retriever.search(query)
            products = found_products
            product_ids = [p["id"] for p in found_products]

            if not found_products:
                content = "No products found matching the query."
            else:
                content = json.dumps(found_products, indent=2, default=str)

            results.append(ToolMessage(content=content, tool_call_id=call_id))

        elif name == "sql_query":
            if not product_ids:
                content = "No products in memory. Search for a product first."
            else:
                try:
                    rows = sql_tool.execute(args.get("query", ""))
                    if rows:
                        content = json.dumps(rows, indent=2, default=str)
                    else:
                        content = "Query returned 0 rows. Try a different query."
                except Exception as e:
                    content = f"SQL error: {e}"

            results.append(ToolMessage(content=content, tool_call_id=call_id))
        else:
            results.append(ToolMessage(content=f"Unknown tool: {name}", tool_call_id=call_id))

    return {
        "messages": results,
        "products": products,
        "product_ids": product_ids,
    }
