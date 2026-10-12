"""
Filename: __init__.py
Author: Professor Denis O. Núñez
Email: donunez@programmingjourneys.com
Organization: Programming Journeys
Project: Project 09 - Korra: MCP Server and User Interface
Module: Module 09 - Interfacing and Communication
Layer: Application - Agents
Date Created: October 4, 2026
Date Modified: October 4, 2026
Version: M09S04
License: Educational Use

Requirements:
    None

Description:
    Marks react_agent as a regular package, which is what lets pyproject.toml
    declare it and setuptools install it. Without this file the import of
    react_agent.tools.file_stats_tool in graph.py fails.

    It holds no code on purpose. The LangGraph template ships this file
    importing the compiled graph, and that import makes the graph build twice
    on every start: once through this package and once when the server loads
    graph.py by path. Each build constructs its own model and search clients
    and asks the MCP server for its tool list again.

Usage Instructions:
    Nothing here to call. Import the graph from the module that defines it:
        from react_agent.graph import graph
"""
