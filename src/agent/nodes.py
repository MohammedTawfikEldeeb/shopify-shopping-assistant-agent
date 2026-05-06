import json
from functools import partial

import opik
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
    description="Search for products using semantic search. Always provide the query in English — if the user writes in another language (e.g. Arabic), translate their request to English first. Example: 'شنط رجالي' → 'men bags'. Use ONLY when the user wants to find NEW products.",
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
    if products:
        titles = [p['title'] for p in products if p.get('title')]
        parts.append("Previous products: " + ", ".join(titles))
    else:
        parts.append("No products found yet.")

    return "\n".join(parts)


def _format_products_plain(products: list[dict]) -> str:
    """Format product results as short plain text lines for the LLM."""
    if not products:
        return "No products found matching the query in this store's catalog. Tell the user that no matching products were found and offer to help with something else."

    lines = []
    for p in products:
        title = p.get("title", "")
        price = f"${p['price']}" if p.get("price") else ""
        sizes = ", ".join(p.get("available_sizes", [])) or ""
        colors = ", ".join(p.get("available_colors", [])) or ""
        link = p.get("link", "")
        parts = [part for part in [title, price, sizes, colors, link] if part]
        lines.append(" — ".join(parts))

    return "\n".join(lines)


def _format_sql_results_plain(rows: list[dict]) -> str:
    """Format SQL results as short plain text."""
    if not rows:
        return "Query returned 0 rows."
    if len(rows) == 1 and len(rows[0]) == 1:
        key = list(rows[0].keys())[0]
        return f"{key}: {rows[0][key]}"

    lines = []
    for row in rows:
        parts = [f"{k}: {v}" for k, v in row.items()]
        lines.append(" | ".join(parts))
    return "\n".join(lines)


@opik.track(name="llm.agent_invoke", type="llm", tags=["agent", "hakeem"])
async def _agent_llm_invoke(messages: list):
    """Traced LLM call. Input (messages) and output (response) are auto-captured by @opik.track."""
    llm = make_langchain_llm()
    llm_with_tools = llm.bind_tools(TOOLS)
    response = await llm_with_tools.ainvoke(messages)
    return response


@opik.track(name="llm.summarize_invoke", type="llm", tags=["summarize", "hakeem"])
async def _summarize_llm_invoke(messages: list):
    """Traced LLM call. Input (messages) and output (response) are auto-captured by @opik.track."""
    llm = make_langchain_llm()
    response = await llm.ainvoke(messages)
    return response


@opik.track(name="nodes.agent_node", type="llm", tags=["agent", "hakeem"])
@traceable(name="agent_node", run_type="chain", tags=["agent", "hakeem"])
async def agent_node(state: AgentState) -> dict:
    summary = state.get("summary", "")
    products = state.get("products", [])

    context = _build_context(summary, products)
    system_prompt = SYSTEM_PROMPT.prompt.format(context=context, db_schema=DB_SCHEMA)
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = await _agent_llm_invoke(messages)

    return {"messages": [response]}


@opik.track(name="nodes.summarize_node", type="llm", tags=["summarize", "hakeem"])
@traceable(name="summarize_node", run_type="chain", tags=["summarize", "hakeem"])
async def summarize_node(state: AgentState) -> dict:
    summary = state.get("summary", "")

    if summary:
        prompt_text = SUMMARIZE_EXTEND_PROMPT.prompt.format(summary=summary)
    else:
        prompt_text = SUMMARIZE_PROMPT.prompt

    messages = state["messages"]
    summarize_messages = messages + [HumanMessage(content=prompt_text)]

    response = await _summarize_llm_invoke(summarize_messages)

    delete_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]

    return {
        "summary": response.content,
        "messages": delete_messages,
    }


@opik.track(name="nodes.tools_node", type="tool", tags=["tools", "hakeem"])
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
            found_products = await retriever.search(query, top_k=10)

            if found_products:
                products = found_products
                product_ids = [p["id"] for p in found_products]
            else:
                products = []
                product_ids = []

            content = _format_products_plain(found_products)
            results.append(ToolMessage(content=content, tool_call_id=call_id))

        elif name == "sql_query":
            if not product_ids:
                content = "No products in memory. Search for a product first."
            else:
                try:
                    rows = await sql_tool.execute(args.get("query", ""))
                    content = _format_sql_results_plain(rows)
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
