from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import asyncio
import argparse
import os
from dotenv import load_dotenv
from src.cognito_auth import CognitoAuthenticator

# Load environment variables
load_dotenv()

# MCP server URL
http_url = "http://localhost:8080/mcp"

async def use_streamable_http_client(token=None):
    """
    Connect to the MCP server using a token
    
    Args:
        token: Optional token to use for authentication
    """
    if token:
        # Use the provided token
        headers = {"Authorization": f"Bearer {token}"}
        transport = StreamableHttpTransport(url=http_url, headers=headers)
        client = Client(transport)
    else:
        # This will fail due to missing authentication
        client = Client(http_url)
    
    try:
        async with client:
            tools = await client.list_tools()
            print(f"Connected via Streamable HTTP, found tools: {tools}")
            
            # Try using a tool
            result = await client.add(a=10, b=20)
            print(f"10 + 20 = {result}")
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")

async def run_with_m2m_token():
    """
    Get an M2M token from Cognito and use it to connect to the MCP server
    """
    try:
        # Create authenticator
        auth = CognitoAuthenticator()
        
        # Get M2M token
        print("Getting M2M token from Cognito...")
        token_response = auth.get_m2m_token(scopes=["my-api/read"])
        
        # Extract the access token
        token = token_response.get("access_token")
        if not token:
            print("Failed to get access token")
            return
            
        print(f"Successfully obtained access token. Token expires in {token_response.get('expires_in')} seconds")
        
        # Use the token to connect to the MCP server
        await use_streamable_http_client(token)
    except Exception as e:
        print(f"Error getting M2M token: {str(e)}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Client Example")
    parser.add_argument("--token", help="Bearer token to use for authentication")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.token:
        # Use the provided token
        print(f"Using provided token")
        asyncio.run(use_streamable_http_client(args.token))
    else:
        # Get an M2M token from Cognito
        print("No token provided. Getting M2M token from Cognito...")
        asyncio.run(run_with_m2m_token())
