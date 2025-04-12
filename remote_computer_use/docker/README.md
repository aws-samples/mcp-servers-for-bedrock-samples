## Build and run a ubuntu 24.04 sandbox in docker container

### Prequisite
1. Install docker-compose if you did not install it.
```bash
curl -SL https://github.com/docker/compose/releases/download/v2.35.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

2. Start container
```bash
docker-compose up -d
```

###  Add below json to your client to install MCP Server,
- Change the path to the remote_computer_use/server_claude.py. 
- If you run the VNC container in a seperate EC2, please change VNC_HOST to the actual ip address.
```json
{
"mcpServers": {
		"computer_use_docker": {
			"command": "uv",
			"env": {
				"VNC_HOST":"127.0.0.1",
				"VNC_PORT":"5901",
				"VNC_USERNAME":"vnc_user",
				"VNC_PASSWORD":"12345670",
				"PEM_FILE":"",
				"SSH_PORT":"2222",
				"DISPLAY_NUM":"1",
				"WIDTH":"1024",
                "HEIGHT":"768"
			},
			"args": [
				"--directory",
				"/absolute_path/to/remote_computer_use",
				"run",
				"server_claude.py"
			]
		}
   }
}
```

### Other commands
1. Stop container
```bash
docker-compose down
```
2. View logs of container
```bash
docker-compose logs -f
```