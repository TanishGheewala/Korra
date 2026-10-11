"""
Filename: FA26_MD_06_S03_chatbot.py
Project: Project 08 - Korra Tools
Based on the Project 06 starter by Professor Denis O. Nunez,
Programming Journeys. License: Educational Use.

Adaptation for Tanish Gheewala: retains Gemini and Tavily, adds the supplied
C file-statistics wrapper, and logs actual tool calls and results.

The compiled graph sends each user message to Gemini, executes requested
tools, then returns their results to Gemini for its final response. Each
request is independent; no cross-turn persistence is enabled.

Configuration: GOOGLE_API_KEY and TAVILY_API_KEY in .env beside this file,
or supplied as process environment variables by Docker Compose.
Run: python FA26_MD_06_S03_chatbot.py
See README.md for Docker build, file layout, and evidence prompts.
"""

# Project 08 adaptation: Gemini, Tavily, C file statistics, and visible tool traces.

# ============================================================
# IMPORTS
# ============================================================

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from tools.file_stats_tool import analyze_file_statistics
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition


# ============================================================
# EXCEPTIONS
# ============================================================

class ConfigError(Exception):
    """Raised when a required API key is missing from the environment."""
    pass


# ============================================================
# CONFIGURATION CONSTANTS
# ============================================================

DEFAULT_MODEL = "gemini-3.5-flash-lite"
MAX_SEARCH_RESULTS = 2         # Two results keep the context short and the reply fast
EXIT_COMMANDS = {"quit", "exit", "q"}

# Anchored to the script so the diagram lands beside it, the way .env is read
# from beside it. A bare relative path would follow the working directory and
# leave the student hunting for the file.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "output", "chatbot_graph.png")


# ============================================================
# LOGGER
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# These libraries log every HTTP call, which buries our own messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx2").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


# ============================================================
# ENVIRONMENT
# ============================================================

GOOGLE_API_KEY = None
TAVILY_API_KEY = None


def configure() -> None:
    """
    Load the .env file and confirm both API keys are present.

    Called at import, before the graph is built, because ChatGoogleGenerativeAI and
    TavilySearch both read their key while being constructed. Loading later
    would leave the graph asking for a key that is not there yet.

    Raises:
        ConfigError: If GOOGLE_API_KEY or TAVILY_API_KEY is not set.

    Returns:
        None
    """
    global GOOGLE_API_KEY, TAVILY_API_KEY

    # override=False keeps a key already exported in the shell
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=False)

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    missing = [
        name
        for name, value in (("GOOGLE_API_KEY", GOOGLE_API_KEY),
                            ("TAVILY_API_KEY", TAVILY_API_KEY))
        if not value
    ]
    if missing:
        message = "Missing %s in your environment (.env)" % ", ".join(missing)

        # Logged as well as raised: the traceback tells a developer where it
        # broke, this line tells a student what to go and fix
        logger.error("%s", message)
        raise ConfigError(message)


# SE-04 exemption - Entry Point. This file is both the program a student runs
# and the module LangGraph Studio imports. The graph below is built while this
# module loads, and building it constructs the model and search clients, which
# read their keys on construction. So the environment has to be loaded here,
# before that line, rather than from main().
configure()


# ============================================================
# STATE DEFINITION
# ============================================================

class State(TypedDict):
    """
    State schema for the chatbot graph.

    Attributes:
        messages: Chat messages, merged by add_messages as the graph runs
    """

    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================
# GRAPH INITIALIZATION
# ============================================================

def initialize_chatbot() -> CompiledStateGraph:
    """
    Build and compile the conversation graph.

    The graph sends every turn to the model first. If the model asks for a
    web search, the conditional edge routes to the tool node and back, so a
    search result becomes part of the same conversation rather than a
    separate reply.

    Returns:
        CompiledStateGraph: A graph ready to accept invoke() calls.
    """
    llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, vertexai=False)
    search_tool = TavilySearch(max_results=MAX_SEARCH_RESULTS)

    # Binding advertises the tool to the model so it can request a search
    available_tools = [search_tool, analyze_file_statistics]
    llm_with_tools = llm.bind_tools(available_tools)

    def chatbot(state: State) -> dict[str, list[BaseMessage]]:
        """
        Send the conversation so far to the model and return its reply.

        Args:
            state: Current conversation state containing message history

        Returns:
            dict: The reply, which add_messages appends to the history
        """
        response = llm_with_tools.invoke(state["messages"])
        for call in response.tool_calls:
            logger.info("TOOL CALL: %s %s", call["name"], json.dumps(call["args"]))
        return {"messages": [response]}

    def tools(state: State) -> dict[str, list[BaseMessage]]:
        """
        Execute tool calls and return results.

        Args:
            state: Current conversation state with tool call requests

        Returns:
            dict: Updated state with tool execution results
        """
        tool_node = ToolNode(tools=available_tools)
        result = tool_node.invoke(state)
        for message in result["messages"]:
            logger.info("TOOL RESULT: %s %s", message.name, message.content)
        return result

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tools)

    graph_builder.add_edge(START, "chatbot")

    # tools_condition reads the model's reply and routes to "tools" only
    # when the model actually requested one
    graph_builder.add_conditional_edges("chatbot", tools_condition)

    # A search result goes back to the model so it can answer with it
    graph_builder.add_edge("tools", "chatbot")

    return graph_builder.compile()


# SE-03 exemption - LangGraph Studio resolves the graph by importing this
# module and reading this attribute, so it must exist at module level
graph = initialize_chatbot()


# ============================================================
# GRAPH VISUALIZATION
# ============================================================

def save_graph_visualization() -> None:
    """
    Write a PNG diagram of the graph, if pygraphviz is installed.

    The diagram is a teaching aid, not part of running the chat, so a
    failure here warns and returns instead of stopping the program.

    Returns:
        None
    """
    try:
        png_data = graph.get_graph().draw_png()

        os.makedirs(os.path.dirname(GRAPH_OUTPUT_FILE), exist_ok=True)
        with open(GRAPH_OUTPUT_FILE, "wb") as png_file:
            png_file.write(png_data)

        logger.info("Graph visualization saved: %s", GRAPH_OUTPUT_FILE)
    except Exception as error:
        logger.warning("Could not save graph visualization: %s", error)


# ============================================================
# CHAT INTERFACE
# ============================================================

def extract_reply(message: BaseMessage) -> str:
    """
    Return a printable string for a message the graph produced.

    A message's content is usually a string, but a model that answers in
    parts returns a list of blocks instead. Joining the text blocks keeps
    the caller from having to know which shape it received.

    Args:
        message: The final message from a graph run

    Returns:
        str: The reply text, ready to print.
    """
    content = message.content

    if isinstance(content, str):
        return content.strip()

    # List form: keep the text blocks and drop everything else
    parts = [
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    ]
    return " ".join(part for part in parts if part).strip()


def ask(user_input: str) -> None:
    """
    Send one message to the chatbot and print the reply.

    Args:
        user_input: The user's message text

    Returns:
        None
    """
    try:
        result = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        print("Assistant: " + extract_reply(result["messages"][-1]))
    except Exception as error:
        logger.error("Error during conversation: %s", error)
        print("Assistant: Sorry, I encountered an error. Please try again.")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main() -> None:
    """
    Write the graph diagram, then run the interactive chat loop.

    The environment is already loaded and checked by the time this runs;
    configure() is called while the module loads, so that the graph can be
    built. See the Entry Point exemption in the file header.

    Returns:
        None
    """
    # Optional PNG rendering is omitted from this container workflow.

    current_date = datetime.now().strftime("%B %d, %Y")

    print("=" * 60)
    print("Welcome to Korra - AI Chatbot")
    print("Date: " + current_date)
    print("=" * 60)
    print("Type 'quit', 'exit', or 'q' to leave.")
    print()

    # Ctrl+C is caught around the whole loop, not just around input(), because
    # it can also arrive while the model is still answering. KeyboardInterrupt
    # is not an Exception, so the handler inside ask() would never see it.
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                # Reached when input is piped in and the file ends
                print()
                break

            if user_input.lower() in EXIT_COMMANDS:
                break

            # An empty line is a stray Enter, not a question
            if not user_input:
                continue

            ask(user_input)
            print()
    except KeyboardInterrupt:
        print()

    print("Goodbye! Thanks for chatting.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
