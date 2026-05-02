import json

import opik

from src.infrastructure.llm.interface import LLMInterface
from src.infrastructure.llm.factory import create_llm
from src.config import get_settings
from src.observability.opik_utils import configure as configure_opik
from src.observability.prompt_versioning import Prompt
from .memory import ShortTermMemory
from .tools import ProductRetriever, SQLQueryTool
from .schemas import AgentDecision


DB_SCHEMA = """
- products(id UUID, store_id UUID, shopify_product_id BIGINT, handle TEXT, title TEXT, description TEXT, vendor TEXT, product_type TEXT, published_at TIMESTAMPTZ, sync_status TEXT, raw_payload JSONB)
- product_variants(id UUID, product_id UUID, shopify_variant_id BIGINT, title TEXT, sku TEXT, option1 TEXT, option2 TEXT, option3 TEXT, available BOOLEAN, price NUMERIC, compare_at_price NUMERIC, requires_shipping BOOLEAN, taxable BOOLEAN, grams INT, position INT)
- product_images(id UUID, product_id UUID, shopify_image_id BIGINT, src TEXT, alt_text TEXT, position INT, width INT, height INT)
- product_options(id UUID, product_id UUID, name TEXT, position INT)
- product_option_values(id UUID, option_id UUID, value TEXT, position INT)
"""

_SYSTEM_PROMPT_TEMPLATE = """You are a helpful shopping assistant. You help users find products and then answer follow-up questions about them.

{context}

Database Schema:
{db_schema}

Actions:
1. retrieve - Use ONLY when the user wants to find NEW products. Provide a concise semantic search query in `content`.
2. sql_query - Use when the user asks about details of products already found above (options, sizes, colors, prices, variants, images, materials). Write a PostgreSQL SELECT query in `content`.
3. answer - Use ONLY for final answers, general chat, or when you don't have enough info.

CRITICAL RULES:
- If previous products are listed above and the user asks about ANY of them, you MUST use action="sql_query".
- When using sql_query, ALWAYS filter by product_id = 'UUID' or product_id IN ('UUID', ...).
- ONLY SELECT queries. Never modify data.
- If a SQL query returns 0 rows, I will tell you and you should try a different query.
- Check BOTH product_options/product_option_values AND product_variants when asked about colors/sizes.

SQL examples:
- Options of a product: SELECT po.name, pov.value FROM product_options po JOIN product_option_values pov ON po.id = pov.option_id WHERE po.product_id = 'UUID'
- All variants: SELECT title, sku, option1, option2, option3, price, available FROM product_variants WHERE product_id = 'UUID'
- Price of specific variant: SELECT title, price, option1, option2, option3 FROM product_variants WHERE product_id = 'UUID' AND ('White' IN (option1, option2, option3))
"""


class ShoppingAgent:
    def __init__(
        self,
        retriever: ProductRetriever,
        sql_tool: SQLQueryTool,
        llm: LLMInterface | None = None,
    ):
        configure_opik()
        self.llm = llm or create_llm(get_settings().llm.provider)
        self.memory = ShortTermMemory()
        self.retriever = retriever
        self.sql_tool = sql_tool
        self._system_prompt = Prompt(
            name="shopping-agent-system-prompt",
            prompt=_SYSTEM_PROMPT_TEMPLATE,
        )

    def _build_system_prompt(self) -> str:
        parts = [self.memory.get_context(), ""]
        if self.memory.last_products:
            lines = ["Previously found products:"]
            for p in self.memory.last_products:
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
        context = "\n".join(parts)
        return self._system_prompt.prompt.format(context=context, db_schema=DB_SCHEMA)

    @opik.track(name="agent.chat", type="general")
    async def chat(self, user_message: str) -> str:
        self.memory.add("user", user_message)

        for turn in range(3):
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": user_message},
            ]

            decision = self._make_decision(messages)

            if decision.action == "retrieve":
                response = await self._handle_retrieve(decision.content)
                return await self._finalize(response)

            if decision.action == "sql_query":
                observation = await self._execute_sql(decision.content)
                if observation["rows"]:
                    response = self._summarize_results(user_message, json.dumps(observation["rows"], indent=2, default=str))
                    return await self._finalize(response)
                user_message = f"I tried this SQL: {decision.content}\nResult: {observation['message']}\nOriginal question: {user_message}\nPlease try again with a corrected query."

            elif decision.action == "answer":
                return await self._finalize(decision.content)

        return await self._finalize("Sorry, I couldn't find that information after multiple attempts.")

    async def _finalize(self, response: str) -> str:
        self.memory.add("assistant", response)
        await self._maybe_summarize()
        return response

    async def _maybe_summarize(self):
        if not self.memory.should_summarize():
            return
        oldest = self.memory.messages[:-2]
        new_summary = self._summarize_conversation(self.memory.summary, oldest)
        self.memory.summary = new_summary
        self.memory.messages = self.memory.messages[-2:]

    @opik.track(name="agent.summarize_conversation", type="llm")
    def _summarize_conversation(self, old_summary: str, messages: list) -> str:
        msgs_text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        prompt = [
            {"role": "system", "content": "Summarize this conversation very briefly (1-2 sentences). Keep only key facts: products mentioned, user preferences, what was asked about."},
            {"role": "user", "content": f"Old summary: {old_summary}\n\nNew messages:\n{msgs_text}"},
        ]
        response = self.llm.chat(prompt)
        return response.choices[0].message.content

    @opik.track(name="agent.make_decision", type="tool", capture_output=False)
    def _make_decision(self, messages: list) -> AgentDecision:
        structured = self.llm.with_structured_output(AgentDecision)
        return structured.invoke(messages)

    async def _handle_retrieve(self, search_query: str) -> str:
        products = await self.retriever.search(search_query)
        self.memory.set_products(products)
        if not products:
            return "I couldn't find any products matching your request."
        summary_lines = []
        for p in products:
            line = f"- {p['title']} (ID: {p['id']}"
            if p.get("price"):
                line += f", Price: ${p['price']}"
            if p.get("link"):
                line += f", Link: {p['link']}"
            line += ")"
            summary_lines.append(line)
        summary = "\n".join(summary_lines)
        return f"Here are some products I found:\n{summary}"

    async def _execute_sql(self, query: str) -> dict:
        if not self.memory.last_product_ids:
            return {"rows": [], "message": "No products in memory. Search for a product first."}
        try:
            rows = self.sql_tool.execute(query)
            if rows:
                return {"rows": rows, "message": f"Found {len(rows)} row(s)"}
            return {"rows": [], "message": "Query returned 0 rows. Try a different query."}
        except Exception as e:
            return {"rows": [], "message": f"SQL error: {e}"}

    @opik.track(name="agent.summarize_results", type="llm")
    def _summarize_results(self, user_message: str, result_text: str) -> str:
        fmt_messages = [
            {"role": "system", "content": "Summarize the following database results in a friendly, concise way for the user. Include specific prices, sizes, colors etc."},
            {"role": "user", "content": f"User asked: {user_message}\nResults:\n{result_text}"},
        ]
        response = self.llm.chat(fmt_messages)
        return response.choices[0].message.content
