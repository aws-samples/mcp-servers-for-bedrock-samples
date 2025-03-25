# DeepSeek Planner MCP Server

An MCP (Model Context Protocol) server that provides planning and coding assistance using the DeepSeek model hosted on Amazon Bedrock.

## Features

- **Project Planning**: Generate detailed project plans based on requirements
- **Code Generation**: Create code in various programming languages
- **Code Review**: Get feedback on your code
- **Code Explanation**: Understand complex code
- **Code Refactoring**: Improve your code quality

## Prerequisites

- Python 3.8 or higher
- AWS account with access to Amazon Bedrock
- AWS credentials with permissions to invoke the DeepSeek model

## Installation

1. Clone this repository
2. Create and activate a virtual environment:
   ```
   uv sync
   source venv/bin/activate
   ```

## Usage

### Running the server

```
python src/server.py
```

### Environment Variables

The server requires the following environment variables:

```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1  # Optional, defaults to us-east-1
AWS_SESSION_TOKEN=your_session_token  # Optional, only needed for temporary credentials
```

### Using with Claude Desktop

1. Open your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the DeepSeek Planner server configuration:
   ```json
   {
     "mcpServers": {
       "deepseek-planner": {
         "command": "uv",
          "args": [
                "--directory",
                "/path/to/deepseek-planner/src",
                "run",
                "server.py"
            ],
         "env": {
           "AWS_ACCESS_KEY_ID": "your_access_key_id",
           "AWS_SECRET_ACCESS_KEY": "your_secret_access_key",
           "AWS_REGION": "us-east-1"
         }
       }
     }
   }
   ```

3. Restart Claude Desktop

### Available Tools

1. **generate_plan**: Create a detailed project plan based on requirements
2. **generate_code**: Generate code based on requirements
3. **review_code**: Review code and provide feedback
4. **explain_code**: Explain code in detail
5. **refactor_code**: Refactor code to improve quality

## License

MIT
