# Nova ACT MCP Server

This is a Model Context Protocol (MCP) server that integrates with AWS [Nova ACT](https://github.com/aws/nova-act/tree/main), allowing AI agents to perform actions through the Nova ACT framework.


## Installation
### Setup

```bash
# Clone the repository
cd nova-act-mcp-server

# Install dependencies
uv sync
source .venv/bin/activate
```

## Usage

### Setting up with MCP

```json
{
  "mcpServers": {
    "nova-act": {
      "command": "uv",
      "args": ["--directory","/absolute/path/to/src","run","server.py"],
      "env": {
        "NOVA_ACT_API_KEY": "your-nova-act-api-key-here"
      }
    }
  }
}
```

headless
```json
{
  "mcpServers": {
    "nova-act": {
      "command": "uv",
      "args": ["--directory","/absolute/path/to/src","run","server.py"],
      "env": {
        "NOVA_ACT_API_KEY": "your-nova-act-api-key-here",
        "headless":true
      }
    }
  }
}
```

## License

MIT
