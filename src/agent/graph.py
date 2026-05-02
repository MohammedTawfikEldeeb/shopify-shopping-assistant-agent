from functools import partial
from langgraph.graph import StateGraph, START, END

from src.agent.states import AgentState
from src.agent.nodes import agent_node, summarize_node, tools_node
from src.agent.tools import ProductRetriever, SQLQueryTool


def build_graph(retriever: ProductRetriever, sql_tool: SQLQueryTool):
    builder = StateGraph(AgentState)

    builder.add_node("summarize", summarize_node)
    builder.add_node("agent", agent_node)

    tool_node_bound = partial(tools_node, retriever=retriever, sql_tool=sql_tool)
    builder.add_node("tools", tool_node_bound)

    def should_summarize(state: AgentState) -> str:
        if len(state["messages"]) > 8:
            return "summarize"
        return "agent"

    builder.add_conditional_edges(
        START,
        should_summarize,
        {"summarize": "summarize", "agent": "agent"},
    )
    builder.add_edge("summarize", "agent")

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    builder.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "agent")

    return builder.compile()
