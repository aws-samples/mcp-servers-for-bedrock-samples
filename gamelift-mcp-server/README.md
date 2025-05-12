# GameLift MCP Server

This project provides a simple MCP server for managing AWS GameLift fleets and container fleets. It exposes several API endpoints for querying fleet information, attributes, and echo testing.

## Features
- Query GameLift fleets in a specific AWS region
- Query GameLift container fleets in a specific AWS region
- Get detailed attributes for a given fleet or container fleet
- Simple echo endpoint for testing

## Requirements
- Python 3.12+
- AWS credentials with GameLift permissions
- The following Python packages:
  - boto3
  - httpx
  - mcp.server.fastmcp (custom or third-party)

## Environment Variables
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

## How to Run
1. Install dependencies:
   ```bash
   pip install boto3 httpx
   # Install mcp.server.fastmcp as required
   ```
2. Set AWS credentials in your environment:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   ```
3. Start the MCP server:
   ```bash
   python src/gamelift_mcp_server.py
   ```

## API Endpoints (Tools)
- `echo(message: str) -> str`: Returns a test echo message.
- `get_game_lift_fleets(region: str = 'us-east-1') -> str`: List all GameLift fleets in the specified region.
- `get_gamelift_container_fleets(region: str = 'us-east-1') -> str`: List all GameLift container fleets in the specified region.
- `get_fleet_attributes(fleet_id: str, region: str = 'us-east-1') -> str`: Get attributes for a specific GameLift fleet.
- `get_container_fleet_attributes(fleet_id: str, region: str = 'us-east-1') -> str`: Get attributes for a specific GameLift container fleet.

## Config Mcp Server
```
{
  "mcpServers": {
    "gamelift_mcp_server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/gamelift-mcp-server/src",
        "run",
        "gamelift_mcp_server.py"
      ],
      "env": {
        "AWS_ACCESS_KEY_ID": "xxxx",
        "AWS_SECRET_ACCESS_KEY": "xxxxx",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```


## Notes
- Make sure your AWS account has the necessary GameLift permissions.
- The MCP server is designed for internal or development use.

---

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
