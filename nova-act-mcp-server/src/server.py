#!/usr/bin/env python3
"""
MCP server that wraps the Nova ACT SDK, allowing agents to perform browser actions via Nova ACT.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


from mcp.server.fastmcp import FastMCP, Context
from nova_act import NovaAct

# Initialize FastMCP server
mcp = FastMCP("nova-act")

# Global client instance
nova_client = None

class ActionResult(BaseModel):
    response: str

# @mcp.tool()
async def initialize_nova_act(starting_page: str) -> str:
    """Initialize the Nova ACT client with starting page to browse.
    
    Args:
        starting_page: Starting web page url for the browser, must start with or http:// or https:// 
        
    Returns:
        A confirmation message
    """
    global nova_client
    try:
        if nova_client:
            nova_client.stop()
            nova_client = None
        nova_client = NovaAct(starting_page=starting_page,
                                headless=os.environ.get('headless',False)
        )
        return "Nova ACT client successfully initialized"
    except Exception as e:
        return f"Failed to initialize Nova ACT client: {str(e)}"

@mcp.tool()
async def perform_action(starting_page: str, commands: List[str]) -> str:
    """Perform an action using Nova ACT.
    
    Args:
        starting_page: Starting web page url for the browser, must start with or http:// or https:// 
        commands: A array list of action commands that each command actuates a natural language command in the web browser, e.g. ["search for a coffee maker","select the first result","scroll down or up until you see 'add to cart' and then click 'add to cart'"]
        
    Returns:
        The result of the action
    """
    try:
        nova_client = NovaAct(starting_page=starting_page,
                                headless=os.environ.get('headless',False)
        )
        nova_client.start()
        final_reponse = []
        for idx, cmd in enumerate(commands):
            command = cmd.strip().lower()
            action_result = nova_client.act(command,schema=ActionResult.model_json_schema())
            if not action_result.matches_schema:
                final_reponse.append(f"action [{idx+1}] result: None")
            else:
                final_reponse.append(f"action [{idx+1}] result: {action_result.response}")
        nova_client.stop()
        return "\n".join(final_reponse)
    except Exception as e:
        return f"Failed to perform action: {str(e)}"


def main():
    starting_page = "https://www.amazon.com"
    commands = ["search men shoes","click the first item","get me the price"]
    try:
        nova_client = NovaAct(starting_page=starting_page,
                                headless=os.environ.get('headless',False)
        )
        nova_client.start()
        final_reponse = []
        for idx, cmd in enumerate(commands):
            command = cmd.strip().lower()
            action_result = nova_client.act(command,schema=ActionResult.model_json_schema())
            if not action_result.matches_schema:
                final_reponse.append(f"action [{idx+1}] result: None")
            else:
                final_reponse.append(f"action [{idx+1}] result: {action_result.response}")
        nova_client.stop()
        return "\n".join(final_reponse)
    except Exception as e:
        return f"Failed to perform action: {str(e)}"
    # return await perform_action(starting_page, actions)

if __name__ == "__main__":
    if not os.environ.get("NOVA_ACT_API_KEY"):
        print("NOVA_ACT_API_KEY are not set. Please set NOVA_ACT_API_KEY environment variables.")
        exit(1)
    # Initialize and run the server
    mcp.run(transport='stdio')
    # main()
    # asyncio.run(main())
