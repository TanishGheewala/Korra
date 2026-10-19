"""Project 06 conversation loop's graph, now accepting a checkpointer."""
import os
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from .config import make_model


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_chat(checkpointer, *, model=None, with_search=True):
    model = model or make_model()
    tools = [TavilySearch(max_results=2)] if with_search and os.getenv("TAVILY_API_KEY") else []
    if tools:
        model = model.bind_tools(tools)
    system = SystemMessage(content=(
        "You are Korra. Answer briefly, using only this conversation's history "
        "for facts the user told you. If asked for a name or personal fact that "
        "does not appear in this thread, say you do not know; never guess."
    ))

    def chatbot(state: State, config: RunnableConfig):
        return {"messages": [model.invoke([system, *state["messages"]], config=config)]}

    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")
    return builder.compile(checkpointer=checkpointer)
