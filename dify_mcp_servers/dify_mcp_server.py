from typing import Any, Dict, Optional
import httpx
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("dify")

# Constants
DIFY_API_BASE = "https://api.dify.ai/v1"   # You can get it from dify console.
DEFAULT_API_KEY = "API_KEY "  # You can get the API_KEY from dify console.

async def make_dify_request(endpoint: str, data: Dict[str, Any], api_key: str = DEFAULT_API_KEY, streaming: bool = True) -> Dict[str, Any]:
    """Make a request to the Dify API with proper error handling.
    
    Args:
        endpoint: API endpoint to call
        data: Request payload
        api_key: Dify API key
        streaming: Whether to use streaming response mode
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Set response mode based on streaming parameter
    if "response_mode" not in data:
        data["response_mode"] = "streaming" if streaming else "blocking"
    
    url = f"{DIFY_API_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

@mcp.tool()
async def run_workflow(inputs: Dict[str, str], user_id: Optional[str] = "abc-123", api_key: Optional[str] = None) -> str:
    """Run a Dify workflow with the provided inputs.
    
    Args:
        inputs: Dictionary of input parameters for the workflow
        user_id: Optional user identifier for the request
        api_key: Optional API key to override the default
    """
    data = {
        "inputs": inputs,
        "response_mode": "blocking",  # Using blocking for MCP tool response
        "user": user_id
    }
    
    result = await make_dify_request("workflows/run", data, api_key or DEFAULT_API_KEY, streaming=False)
    
    if "error" in result:
        return f"Error: {result['error']}\n{result.get('details', '')}"
    
    # You shoud replace the output processing with your dify workflow input
    try:
        if "data" in result and "outputs" in result["data"] and "advice" in result["data"]["outputs"]:
            advice = result["data"]["outputs"]["advice"]
            return advice
        else:
            return "No advice found in the response."
    except Exception as e:
        return f"Failed to parse response: {str(e)}"

@mcp.tool()
async def chat_completion(message: str, conversation_id: Optional[str] = None, 
                         user_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """Send a message to Dify chat completion API.
    
    Args:
        message: The user message to send
        conversation_id: Optional conversation ID for continuing a conversation
        user_id: Optional user identifier for the request
        api_key: Optional API key to override the default
    """
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking"  # Using blocking for MCP tool response
    }
    
    if user_id:
        data["user"] = user_id
    
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    result = await make_dify_request("chat-messages", data, api_key or DEFAULT_API_KEY, streaming=False)
    
    if "error" in result:
        return f"Error: {result['error']}\n{result.get('details', '')}"
    
    # Extract only the answer from the response
    try:
        answer = result.get("answer", "No answer provided")
        return answer
    except Exception as e:
        return f"Failed to parse response: {str(e)}"

@mcp.tool()
async def get_conversation_history(conversation_id: str, first_id: Optional[str] = None, 
                                  limit: int = 20, api_key: Optional[str] = None) -> str:
    """Retrieve conversation history from Dify.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        first_id: Optional first message ID for pagination
        limit: Maximum number of messages to retrieve (default: 20)
        api_key: Optional API key to override the default
    """
    endpoint = f"conversations/{conversation_id}/messages"
    params = {}
    
    if first_id:
        params["first_id"] = first_id
    
    if limit:
        params["limit"] = limit
    
    headers = {
        "Authorization": f"Bearer {api_key or DEFAULT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{DIFY_API_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            if "data" not in result:
                return "No conversation history found or error retrieving history."
            
            messages = result["data"]
            formatted_messages = []
            
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "No content")
                formatted_messages.append(f"{role.upper()}: {content}")
            
            return "\n\n".join(formatted_messages)
        except Exception as e:
            return f"Failed to retrieve conversation history: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
