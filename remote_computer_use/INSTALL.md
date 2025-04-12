# Computer Use MCP Server - Installation Guide

This guide provides step-by-step instructions for installing and configuring the Computer Use MCP Server.

## Prerequisites

Before you begin, ensure you have the following:  
1. **Remote Desktop on Ubuntu 24.04** You can use an AWS EC2 instance with Ubuntu 24.04
2. **VNC Server** running on your remote Ubuntu machine
3. **xdotool** installed on your remote Ubuntu machine
4. **SSH access** to your remote Ubuntu machine

## Installation Steps

## Install VNC remote desktop on ubuntu 24.04
1. First, update your system packages:
```bash
sudo apt update
sudo apt upgrade
```
- install necessary apps
```bash
sudo apt install -y xdotool
sudo apt install -y scrot
sudo add-apt-repository ppa:mozillateam/ppa && \
sudo apt-get install -y --no-install-recommends \
libreoffice \
firefox-esr 
```

2. Install a Desktop Environment
```bash
sudo apt install xfce4 xfce4-goodies
```

3. Install TigerVNC Server
```bash
sudo apt install tigervnc-standalone-server tigervnc-common
```

4. Set up a password for VNC access:
```bash
vncpasswd
```

5. Create or edit the VNC startup file:
```bash
vim ~/.vnc/xstartup
```
- For Xfce, add the following content:
```bash
#!/bin/sh

unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

[ -x /etc/vnc/xstartup ] && exec /etc/vnc/xstartup
[ -r $HOME/.Xresources ] && xrdb $HOME/.Xresources

export XKL_XMODMAP_DISABLE=1
startxfce4
```

6. Make the startup file executable:
```bash
chmod +x ~/.vnc/xstartup
```

7. Starting the VNC Server
```bash
tigervncserver -xstartup /usr/bin/startxfce4 -SecurityTypes VncAuth,TLSVnc -geometry 1024x768 -localhost no :1
```

8. Open (TCP : 5901) in your Securty Group of EC2 

9. Optional: stop the VNC server
```bash
vncserver -kill :*
```

### 4. Test Your Connection
Edit the `.env` file created by the setup script:

```bash
# VNC Connection Settings
VNC_HOST=192.168.1.100  # Replace with your Ubuntu server IP
VNC_PORT=5900           # Default VNC port
VNC_USERNAME=ubuntu     # Your username
VNC_PASSWORD=password   # Your VNC password
PEM_FILE=your_pem_file.pem
DISPLAY_NUM=1
# SSH Connection Settings (uses same host as VNC)
SSH_PORT=22             # Default SSH port
```
Before running the MCP server, test your VNC and SSH connections:

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the connection test
./test_connection.py
```

This will verify that:
- Your VNC connection works and can capture screenshots
- Your SSH connection works

If any tests fail, check the error messages and troubleshoot accordingly.


This will start the MCP Inspector interface where you can test the server's tools.


###  Add below json to your client to install MCP Server,
this `server_claude.py` works better for Claude 3.5/3.7, if you want to use other models, please change the run command to run `server.py` instead.
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
                "WIDTH":"1024",
                "HEIGHT":"768",
                "SSH_PORT":"22",
                "DISPLAY_NUM":"1"
            },
            "args": [
                "--directory",
                "/absolute_path_to/remote_computer_use",
                "run",
                "server_claude.py"
            ]
        }
    }
}
```