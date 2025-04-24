## Time server
通过这个mcp server让Agent知道当前时间，使用方式: 
git clone repo到本地或者服务器上:  
在MCP clien中添加
```json
{"mcpServers": 
	{ "time": 
		{ "command": "uv", 
		"args": ["--directory","/path/to/time_server/src",
		"run",
			"server.py"]
		 } 
		}
	}
```



