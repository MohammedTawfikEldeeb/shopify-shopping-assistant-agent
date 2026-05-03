import json
import opik
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, AnyMessage
from langgraph.graph.message import RemoveMessage

from src.agent.graph import build_graph
from src.agent.tools import ProductRetriever, SQLQueryTool
from src.observability.opik_utils import configure as configure_opik


class _MemoryProxy:
    def __init__(self, products: list[dict]):
        self.last_products = products


def _message_to_dict(msg: AnyMessage) -> dict | None:
    """Serialize a LangChain message to a dict. Skip RemoveMessage."""
    if isinstance(msg, RemoveMessage):
        return None
    return {
        "type": msg.type,
        "content": msg.content,
        "additional_kwargs": msg.additional_kwargs,
        "id": getattr(msg, "id", None),
        "tool_call_id": getattr(msg, "tool_call_id", None),
    }


def _dict_to_message(data: dict) -> AnyMessage:
    """Deserialize a dict back to a LangChain message."""
    msg_type = data.get("type")
    content = data.get("content", "")
    additional_kwargs = data.get("additional_kwargs", {})
    msg_id = data.get("id")
    tool_call_id = data.get("tool_call_id")

    kwargs = {"content": content, "additional_kwargs": additional_kwargs}
    if msg_id:
        kwargs["id"] = msg_id

    if msg_type == "human":
        return HumanMessage(**kwargs)
    elif msg_type == "ai":
        return AIMessage(**kwargs)
    elif msg_type == "tool":
        if tool_call_id:
            kwargs["tool_call_id"] = tool_call_id
        return ToolMessage(**kwargs)
    elif msg_type == "system":
        return SystemMessage(**kwargs)
    else:
        return HumanMessage(**kwargs)


def _serialize_state(state: dict) -> dict:
    """Convert agent state into JSON-serializable dict."""
    serialized = {}
    for key, value in state.items():
        if key == "messages" and isinstance(value, list):
            serialized[key] = [
                m_dict for m in value if (m_dict := _message_to_dict(m)) is not None
            ]
        else:
            serialized[key] = value
    return serialized


def _deserialize_state(state_dict: dict) -> dict:
    """Convert serialized dict back to agent state with proper message objects."""
    deserialized = dict(state_dict)
    if "messages" in deserialized and isinstance(deserialized["messages"], list):
        deserialized["messages"] = [_dict_to_message(m) for m in deserialized["messages"]]
    return deserialized


class ShoppingAgent:
    def __init__(
        self,
        retriever: ProductRetriever,
        sql_tool: SQLQueryTool,
    ):
        configure_opik()
        self.retriever = retriever
        self.sql_tool = sql_tool
        self.graph = build_graph(retriever, sql_tool)

    @opik.track(name="agent.chat", type="general")
    async def chat(self, user_message: str) -> str:
        """Legacy single-turn chat without session persistence."""
        state = {
            "messages": [HumanMessage(content=user_message)],
            "summary": "",
            "products": [],
            "product_ids": [],
        }
        config = {
            "run_name": "agent.chat",
            "tags": ["hakeem", "shopping-agent"],
        }
        result = await self.graph.ainvoke(state, config=config)

        for msg in reversed(result["messages"]):
            msg_type = getattr(msg, "type", None)
            if msg_type == "ai" and not getattr(msg, "tool_calls", None):
                return msg.content

        return "Sorry, I couldn't process that."

    @opik.track(name="agent.chat_with_session", type="general")
    async def chat_with_session(
        self,
        user_message: str,
        session_state: dict | None = None,
    ) -> tuple[str, list[dict], dict]:
        """Session-aware chat that loads/saves state and returns the new state for persistence."""
        if session_state is not None:
            deserialized = _deserialize_state(session_state)
            state = {
                "messages": list(deserialized.get("messages", [])) + [HumanMessage(content=user_message)],
                "summary": deserialized.get("summary", ""),
                "products": deserialized.get("products", []),
                "product_ids": deserialized.get("product_ids", []),
            }
        else:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "summary": "",
                "products": [],
                "product_ids": [],
            }

        config = {
            "run_name": "agent.chat_with_session",
            "tags": ["hakeem", "shopping-agent"],
        }
        result = await self.graph.ainvoke(state, config=config)
        serialized_state = _serialize_state(result)

        products = result.get("products", [])
        for msg in reversed(result["messages"]):
            msg_type = getattr(msg, "type", None)
            if msg_type == "ai" and not getattr(msg, "tool_calls", None):
                return msg.content, products, serialized_state

        return "Sorry, I couldn't process that.", products, serialized_state

    @property
    def memory(self):
        # Legacy property - not used in session mode
        return _MemoryProxy([])
