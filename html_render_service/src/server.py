#!/usr/bin/env python3
"""
Flask Web Service Server
It is a web server tool to generate and render web page from Markdown files and html files.
"""
import os
import asyncio
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any, List
import io
import json
import requests
from mcp.server.fastmcp import FastMCP, Image, Context

ENDPOINT = os.environ.get("endpoint","http://127.0.0.1:5006")

@dataclass
class AppContext:
    """Application context for lifespan management"""
    ready_status: bool
    
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Application lifespan management context manager.

    Args:
        server: FastMCP server instance

    Yields:
        AppContext: Application context with ready_status
    """
    try:
        response = requests.get(f"{ENDPOINT}/")
        response.raise_for_status()
        yield AppContext(ready_status=True)

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error connecting to server: {e}")
    
# Create MCP server
mcp = FastMCP(
    "Flask Web Service Server",
    app_lifespan=app_lifespan,
    dependencies=['requests'])

@mcp.tool()
async def render_markdown(file_name:str, markdown_content: str) -> str:
    """
    uploads markdown it to a server.
    
    Args:
        file_name: Name of the markdown file to be rendered
        markdown_content: Markdown content to be rendered
        
    Returns:
        URL string to access the rendered HTML page
    """
    try:
        response = requests.post(f"{ENDPOINT}/upload_markdown", json={"file_name": file_name, "file_content": markdown_content})
        response.raise_for_status()
        return response.json()['url']
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error uploading HTML file: {e}")

@mcp.tool()
async def render_html(file_name:str, html_content: str) -> str:
    """
    Upload the HTML content to a server.
    
    Args:
        file_name: Name of the HTML file to be rendered
        html_content: HTML content  to be rendered
        
    Returns:
        URL string to access the rendered HTML page
    """
    try:
        response = requests.post(f"{ENDPOINT}/upload_html", json={"file_name": file_name, "file_content": html_content})
        response.raise_for_status()
        return response.json()['url']
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error uploading HTML file: {e}")
    

if __name__ == "__main__":
    # print(render_markdown("test.md","## abcd"))
    # print(render_html("test2.html","abcd2"))
    mcp.run()
