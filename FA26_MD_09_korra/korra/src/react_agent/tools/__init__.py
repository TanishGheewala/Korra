"""
Filename: __init__.py
Author: Professor Denis O. Núñez
Email: donunez@programmingjourneys.com
Organization: Programming Journeys
Project: Project 09 - Korra: MCP Server and User Interface
Module: Module 09 - Interfacing and Communication
Layer: Application - Tools
Date Created: October 4, 2026
Date Modified: October 4, 2026
Version: M09S04
License: Educational Use

Requirements:
    None

Description:
    Marks react_agent.tools as a regular package so the wrapper beside it can
    be imported as react_agent.tools.file_stats_tool. pyproject.toml lists
    react_agent.tools explicitly, which is what packages the folder on
    install.

    Removing this file was tested and the import still resolved, because
    Python then treats the folder as a namespace package. The file is kept
    because the packaging is declared explicitly rather than discovered.

    It holds no code on purpose. Importing the wrapper here would not analyze
    anything, but it would load that module whenever react_agent.tools is
    touched, instead of when the graph asks for the tool.

Usage Instructions:
    Nothing here to call. Import the wrapper from the module that defines it:
        from react_agent.tools.file_stats_tool import analyze_file_statistics
"""
