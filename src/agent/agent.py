from langchain_core.messages import HumanMessage

from src.agent.graph import build_graph
from src.agent.tools import ProductRetriever, SQLQueryTool


class _MemoryProxy:
    def __init__(self, products: list[dict]):
        self.last_products = products


class ShoppingAgent:
    def __init__(
        self,
        retriever: ProductRetriever,
        sql_tool: SQLQueryTool,
    ):
        self.retriever = retriever
        self.sql_tool = sql_tool
        self.graph = build_graph(retriever, sql_tool)
        self._last_state: dict | None = None

    async def chat(self, user_message: str) -> str:
        if self._last_state is None:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "summary": "",
                "products": [],
                "product_ids": [],
            }
        else:
            state = {
                "messages": list(self._last_state["messages"]) + [HumanMessage(content=user_message)],
                "summary": self._last_state.get("summary", ""),
                "products": self._last_state.get("products", []),
                "product_ids": self._last_state.get("product_ids", []),
            }

        result = await self.graph.ainvoke(state)
        self._last_state = result

        for msg in reversed(result["messages"]):
            msg_type = getattr(msg, "type", None)
            if msg_type == "ai" and not getattr(msg, "tool_calls", None):
                return msg.content

        return "Sorry, I couldn't process that."

    @property
    def memory(self):
        products = self._last_state.get("products", []) if self._last_state else []
        return _MemoryProxy(products)
