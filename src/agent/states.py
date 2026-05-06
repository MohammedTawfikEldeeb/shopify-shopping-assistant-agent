from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    summary: str
    products: list[dict]
    product_ids: list[str]
    steps: list[dict]
    product_sets: list[list[dict]]
