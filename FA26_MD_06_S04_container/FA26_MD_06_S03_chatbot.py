"""
Filename: FA26_MD_06_S03_chatbot_v2.py
Author: Professor Denis O. Nunez
Email: donunez@programmingjourneys.com
Organization: Programming Journeys
Project: Project 06 - Korra: AI Chatbot
Module: Module 06 - Programming-Related Topics
Layer: Application - Agents
Date Created: October 8, 2025
Date Modified: September 23, 2026
Version: 3.0
License: Educational Use

Requirements:
    python-dotenv
    langchain-openai
    langchain-tavily
    langchain-core
    langgraph
    typing-extensions

Description:
    Builds Korra, the first AI agent of the framework project, as an
    interactive command-line chatbot. The file assembles a LangGraph state
    graph that routes a conversation between a language model and a web
    search tool, then runs that graph from a terminal prompt.

    It exists so a student can see one complete agent end to end before any
    of the later projects add persistence, tools, oversight or multiple
    agents. Its scope is the graph and the console loop; it owns no storage,
    no web server and no user interface beyond the terminal.

    Framework exemptions claimed by this file:
        LG-01  - Console Application: print() carries the chat interface.
                 Diagnostics and errors still go to the logger.
        SE-03  - LangGraph Studio: the compiled graph is a module-level
                 attribute so Studio can discover it on import.
        SE-04  - Entry Point: configure() runs at import because building
                 that graph constructs the model and search clients, and
                 both read their API key while being constructed.

Usage Instructions:
    1. Create a .env file beside this script containing:
           GOOGLE_API_KEY=your_openai_key
           TAVILY_API_KEY=your_tavily_key
    2. Install dependencies:
           pip install -r requirements.txt
    3. Run the chatbot:
           python FA26_MD_06_S03_chatbot_v2.py
    4. Import the graph without starting the chat:
           from FA26_MD_06_S03_chatbot_v2 import graph
       Importing loads .env, checks both keys, and builds the graph. It does
       not write the diagram or start the chat loop; main() does those.
       A missing key raises ConfigError naming which one is absent.
"""

# Switched to Gemini

# ============================================================
# IMPORTS
# ============================================================

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
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

DEFAULT_MODEL = "gpt-4o-mini"  # Small, inexpensive model suited to classroom use
TEMPERATURE = 0.7              # High enough to vary replies, low enough to stay on topic
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

    Called at import, before the graph is built, because ChatOpenAI and
    TavilySearch both read their key while being constructed. Loading later
    would leave the graph asking for a key that is not there yet.

    Raises:
        ConfigError: If GOOGLE_API_KEY or TAVILY_API_KEY is not set.

    Returns:
        None
    """
    global GOOGLE_API_KEY, TAVILY_API_KEY

    # override=False keeps a key already exported in the shell
    load_dotenv(override=False)

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
    llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=1.0,
    vertexai=False,
)
    search_tool = TavilySearch(max_results=MAX_SEARCH_RESULTS)

    # Binding advertises the tool to the model so it can request a search
    llm_with_tools = llm.bind_tools([search_tool])

    def chatbot(state: State) -> dict[str, list[BaseMessage]]:
        """
        Send the conversation so far to the model and return its reply.

        Args:
            state: Current conversation state containing message history

        Returns:
            dict: The reply, which add_messages appends to the history
        """
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def tools(state: State) -> dict[str, list[BaseMessage]]:
        """
        Execute tool calls and return results.

        Args:
            state: Current conversation state with tool call requests

        Returns:
            dict: Updated state with tool execution results
        """
        tool_node = ToolNode(tools=[search_tool])
        return tool_node.invoke(state)

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
    save_graph_visualization()

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
