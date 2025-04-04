#!/usr/bin/env python3
"""
Computer Use MCP Server
Provides tools for controlling a remote Ubuntu desktop via VNC and xdotool
"""
import os
import asyncio
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any, List
import io
from mcp.server.fastmcp import FastMCP, Image, Context
from vnc_controller import VNCController
from ssh_controller import SSHController
import time
# import dotenv
# dotenv.load_dotenv()

# Create dataclass for app context
@dataclass
class AppContext:
    """Application context for lifespan management"""
    vnc: VNCController
    ssh: SSHController
    display_num : str

# Define lifespan for connection management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage VNC and SSH connections lifecycle
    
    Args:
        server: FastMCP server instance
        
    Yields:
        AppContext: Application context with VNC and SSH controllers
    """
    # Get credentials from environment variables
    vnc_host = os.environ.get("VNC_HOST")
    vnc_port = int(os.environ.get("VNC_PORT", "5900"))
    vnc_username = os.environ.get("VNC_USERNAME")
    vnc_password = os.environ.get("VNC_PASSWORD")
    pem_file = os.environ.get("PEM_FILE", "")
    ssh_port = int(os.environ.get("SSH_PORT", "22"))
    display_num = os.environ.get("DISPLAY_NUM", "1")

    
    # Validate required environment variables
    if not vnc_host:
        raise ValueError("VNC_HOST environment variable is required")
    if not vnc_password:
        raise ValueError("VNC_PASSWORD environment variable is required")
    if not vnc_username:
        raise ValueError("VNC_USERNAME environment variable is required")
    
    # Initialize controllers
    vnc_controller = VNCController(vnc_host, vnc_port, vnc_username, vnc_password)
    ssh_controller = SSHController(vnc_host, ssh_port, vnc_username, vnc_password,pem_file, display_num)
    
    try:
        # Connect on startup
        vnc_success = await vnc_controller.connect()
        if not vnc_success:
            print("Warning: Failed to connect to VNC server on startup")
            
        ssh_success = await ssh_controller.connect()
        if not ssh_success:
            print("Warning: Failed to connect to SSH server on startup")
        
        # Yield context to server
        yield AppContext(vnc=vnc_controller, ssh=ssh_controller,display_num=display_num)
    finally:
        # Disconnect on shutdown
        await vnc_controller.disconnect()
        await ssh_controller.disconnect()

# Create MCP server
mcp = FastMCP(
    "Computer Use",
    dependencies=["pillow", "paramiko", "vncdotool"],
    lifespan=app_lifespan
)


# Define MCP tools
@mcp.tool()
async def capture_region(ctx: Context,x: int, y: int, w: int, h: int) -> Image:
    """
    Capture screenshot only represents of a region of the remote desktop
    
    Args:
        x: X coordinate (pixels from the left edge)
        y: Y coordinate (pixels from the top edge)
        w: Width of the region
        h: Hight of the region
        
    Returns:
        Image: Screenshot of the remote desktop
    """
    vnc = ctx.request_context.lifespan_context.vnc
    screenshot = await vnc.capture_region(x,y,w,h)
    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def capture_screenshot(ctx: Context) -> Image:
    """
    Capture a screenshot of the remote desktop
    
    Returns:
        Image: Screenshot of the remote desktop
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try:
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")

    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def mouse_double_click(ctx: Context, x: int, y: int) -> Image:
    """
    Double-click the left mouse button at the specified coordinates
    
    Args:
        x: X coordinate (pixels from the left edge)
        y: Y coordinate (pixels from the top edge)
        
    Returns:
        str: execution result
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try:
        await vnc.mouse_click(x, y, 1)
        time.sleep(0.1)
        await vnc.mouse_click(x, y, 1)
        time.sleep(3)
    except:
        raise ValueError(f"Failed to double-click, error:{e}")
    
    return  'Double-click executed, please capture a new screenshot in next turn to see the result'

@mcp.tool()
async def mouse_click(ctx: Context, x: int, y: int, button: int = 1) -> Image:
    """
    Click at the specified coordinates and return a screenshot,
    
    Args:
        x: X coordinate (pixels from the left edge)
        y: Y coordinate (pixels from the top edge)
        button: Mouse button (1=Click the left mouse button, 2=Click the middle mouse button, 3=Click the right mouse button)
        
    Returns:
        Image: Screenshot after clicking
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try:
        await vnc.mouse_click(x, y, button)
        
        # Capture screenshot after clicking
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")
    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def mouse_move(ctx: Context, x: int, y: int) -> Image:
    """
    Move mouse to the specified coordinates and return a screenshot

    Args:
        x: X coordinate (pixels from the left edge)
        y: Y coordinate (pixels from the top edge)
        
    Returns:
        Image: Screenshot after moving mouse
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try:
        await vnc.mouse_move(x, y)
        # Capture screenshot after moving mouse
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")
    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def mouse_scroll(ctx: Context, steps: int = 1, direction: str = "down") -> Image:
    """
    Scroll the mouse wheel and return a screenshot
    
    Args:
        steps: Number of scroll steps
        direction: 'up' or 'down'
        
    Returns:
        Image: Screenshot after scrolling
    """
    vnc = ctx.request_context.lifespan_context.vnc
    
    try:
        await vnc.mouse_scroll(steps, direction)
        
        # Capture screenshot after scrolling
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")
    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def type_text(ctx: Context, text: str) -> Image:
    """
    Type the specified text and return a screenshot
    
    Args:
        text: Text to type
        
    Returns:
        Image: Screenshot after typing text
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try :
        await vnc.type_text(text)
        
        # Capture screenshot after typing
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")
    
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def key_press(ctx: Context, key: str) -> Image:
    """
    Press a key and return a screenshot
    
    Args:
        key: Key to press (e.g., 'enter', 'escape', etc.)
        
    Returns:
        Image: Screenshot after pressing key
    """
    vnc = ctx.request_context.lifespan_context.vnc
    try:
        await vnc.key_press(key)
        
        # Capture screenshot after pressing key
        screenshot = await vnc.capture_screenshot()
    except Exception as e:
        raise ValueError(f"{e}")
    # Convert PIL Image to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    
    return Image(data=img_bytes.getvalue(), format="png")

@mcp.tool()
async def execute_bash(ctx: Context, command: str,restart: bool= False) -> Dict[str, Any]:
    """
    Run commands in a bash shell
    * When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    * You have access to a mirror of common linux and python packages via apt and pip.
    * State is persistent across command calls and discussions with the user.
    * To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    * Please avoid commands that may produce a very large amount of output.
    * Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.    
    Args:
        command: The bash command to run. Required unless the tool is being restarted.
        restart: Specifying true will restart this tool. Otherwise, leave this unspecified. Defaut to False
    Returns:
        dict: Command execution result
    """
    ssh = ctx.request_context.lifespan_context.ssh
    if restart:
        ssh_success = await ssh.connect()
        if not ssh_success:
            return "Failed to connect to SSH server on startup"
    
    result = await ssh.execute_command(f"{command}")
    return result

# Run server if executed directly
if __name__ == "__main__":
    mcp.run()