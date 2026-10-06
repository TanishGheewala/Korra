# ============================================================
# Filename: Dockerfile
# Author: Professor Denis O. Nunez
# Email: donunez@programmingjourneys.com
# Organization: Programming Journeys
# Project: Project 06 - Korra: AI Chatbot
# Module: Module 06 - Programming-Related Topics
# Layer: Deployment - Container
# Date Created: October 15, 2025
# Date Modified: September 23, 2026
# Version: 3.0
# License: Educational Use
#
# Description: Container configuration for the Korra AI chatbot
# ============================================================

# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY FA26_MD_06_S03_chatbot.py .

# Create directory for graph output
RUN mkdir -p /app/output

# Set the default command to run the chatbot
CMD ["python", "FA26_MD_06_S03_chatbot.py"]
