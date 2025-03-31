# Dify MCP Servers Project

An agent developed specifically for Dify, implementing an MCP server. You can integrate your Dify workflow or Dify chat workflow with MCP.

## Development Process

1. Log in to Dify, select the workflow you want to integrate, check the API address, and create a new API_KEY.
2. Test the interface using CLI, referring to the Workflow parameter settings. The parameters in the inputs are the workflow inputs:
```bash
curl -X POST 'https://api.dify.ai/v1/workflows/run' \
--header 'Authorization: Bearer api-key' \
--header 'Content-Type: application/json' \
--data-raw '{
    "inputs": {"ad_data": "你好，请介绍一下自己"},
    "response_mode": "streaming",
    "user": "abc-123"
}'
```
3. Use Amazon Q CLI with the prompt: "The cli.txt file in the project contains a runnable HTTP API request example, please refer to this to generate an MCP server similar to weather.py"
4. weather.py is a sample provided by the MCP official website, so we can reference it to generate our own, or implement it with custom code.

## Setup Instructions

### Dify MCP Server

1. Install the required dependencies:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
pip install -r dify_mcp_server/requirements.txt
```

2. Run the server:
```bash
uv init 
uv venv
source .venv/bin/activate
uv add "mcp[cli]" httpx
uv run dify_mcp_server/dify_mcp_server.py
```

3. Configure MCP Server:
```json
"ad_delivery_data_analysis": {
    "command": "uv",
    "args": [
        "--directory",
        "/Users/lht/Documents/GitHub/dify_mcp_server",
        "run",
        "dify_mcp_server.py"
    ],
    "description": "Analysis advertisement delivery data, get insights, and provide advice",
    "status": 1
} 
```

## Usage

To use an MCP server, you need to connect to it and use the tools and resources it provides. Refer to the documentation of each server for more information on how to use it.
