# Computer Use MCP Server

A Model Context Protocol (MCP) server that enables remote control of an Ubuntu desktop via VNC

## Features

- **Mouse Control**: Move, click, and scroll
- **Keyboard Control**: Type text and press keys
- **Screenshot Capture**: Get visual feedback after each operation

## Prerequisites
- VNC server running on the remote Ubuntu machine
- xdotool installed on the remote Ubuntu machine
- SSH access to the remote Ubuntu machine

## Installation
1. Prepare Desktop
[INSTALL](./INSTALL.md)

2. Add below json to your client to install MCP Server
```json
{
    "mcpServers": {
        "computer_use": {
            "command": "uv",
            "env": {
                "VNC_HOST":"",
                "VNC_PORT":"5901",
                "VNC_USERNAME":"ubuntu",
                "VNC_PASSWORD":"",
                "PEM_FILE":"",
                "SSH_PORT":"22",
                "DISPLAY_NUM":"1"
            },
            "args": [
                "--directory",
                "/absolute_path_to/remote_computer_use",
                "run",
                "server.py"
            ]
        }
    }
}
```

## License

MIT
