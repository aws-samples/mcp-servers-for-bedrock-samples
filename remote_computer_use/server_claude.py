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
import json
from mcp.server.fastmcp import FastMCP, Image, Context
from vnc_controller import VNCController
from ssh_controller import SSHController
from tools.computer import ComputerTool20250124 as ComputerTool
from tools.bash import BashTool
from tools.edit import Command,EditTool
import time
import base64
# from PIL import Image
from tools.computer import Action,Action_20250124,ScrollDirection
import functools
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
    dependencies=["pillow", "paramiko", "vncdotool","python-dotenv"],
    lifespan=app_lifespan
)


def update_docstring_with_display_info(func):
    """更新函数的docstring，替换屏幕分辨率占位符"""
    display_width_px = os.environ.get("WIDTH", "1024")
    display_height_px = os.environ.get("HEIGHT", "768")
    display_num = os.environ.get("DISPLAY_NUM", "1")
    
    if func.__doc__:
        func.__doc__ = func.__doc__.format(
            display_width_px=display_width_px,
            display_height_px=display_height_px,
            display_num=display_num
        )
    return func


def base64_to_pil(base64_str):
    """
    Convert a base64 string to a PIL Image object
    
    Args:
        base64_str (str): The base64 string. If it contains metadata 
                         (like 'data:image/jpeg;base64,'), it will be handled.
    
    Returns:
        fastmcp: The fastmcp Image object
    """
    # If the base64 string includes metadata (data URI), remove it
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    img_data = base64.b64decode(base64_str)
    img = Image(data=img_data, format="png")
    return img

@mcp.tool()
@update_docstring_with_display_info
async def capture_region(ctx: Context,x: int, y: int, w: int, h: int) -> Image:
    """
    Capture screenshot only represents of a region of the remote desktop
    - The screen's resolution is {display_width_px}x{display_height_px}.
    - The display number is {display_num}
    
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
@update_docstring_with_display_info
async def computer( ctx: Context,
                    action: Action_20250124,
                    coordinate: List[int] = None,
                    duration: int | float | None = None,
                    scroll_direction: ScrollDirection | None = None,
                    scroll_amount: int | None = None,
                    text:str = None,
                   ):
    """
    Use a mouse and keyboard to interact with a computer, and take screenshots.
    - This is an interface to a desktop GUI with Linux OS. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.
    - Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.
    - The screen's resolution is {display_width_px}x{display_height_px}.
    - The display number is {display_num}
    - Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.
    - If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.
    - Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.
    - When you do `left_click` or `type` action, please make sure you do `mouse_move` to correct coordinates first.
    
    Args: 
        action: The action to perform. The available actions are:
            * `key`: Press a key or key-combination on the keyboard.
            - This supports xdotool's `key` syntax.
            '  - Examples: "a", "Return", "alt+Tab", "ctrl+s", "Up", "KP_0" (for the numpad 0 key).'
            * `hold_key`: Hold down a key or multiple keys for a specified duration (in seconds). Supports the same syntax as `key`.
            * `type`: Type a string of text on the keyboard.
            * `cursor_position`: Get the current (x, y) pixel coordinate of the cursor on the screen.
            * `mouse_move`: Move the cursor to a specified (x, y) pixel coordinate on the screen.
            * `left_mouse_down`: Press the left mouse button.
            * `left_mouse_up`: Release the left mouse button.
            * `left_click`: Click the left mouse button at the specified (x, y) pixel coordinate on the screen. You can also include a key combination to hold down while clicking using the `text` parameter.
            * `left_click_drag`: Click and drag the cursor from `start_coordinate` to a specified (x, y) pixel coordinate on the screen.
            * `right_click`: Click the right mouse button at the specified (x, y) pixel coordinate on the screen.
            * `middle_click`: Click the middle mouse button at the specified (x, y) pixel coordinate on the screen.
            * `double_click`: Double-click the left mouse button at the specified (x, y) pixel coordinate on the screen.
            * `triple_click`: Triple-click the left mouse button at the specified (x, y) pixel coordinate on the screen.
            * `scroll`: Scroll the screen in a specified direction by a specified amount of clicks of the scroll wheel, at the specified (x, y) pixel coordinate. DO NOT use PageUp/PageDown to scroll.
            * `wait`: Wait for a specified duration (in seconds).
            * `screenshot`: Take a screenshot of the screen.
        coordinate: (x, y): This represents the center of the object. The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=mouse_move` and `action=left_click_drag`.
        duration: The duration to hold the key down for. Required only by `action=hold_key` and `action=wait`
        scroll_amount: The number of 'clicks' to scroll. Required only by `action=scroll`.
        scroll_direction: The direction to scroll the screen. Required only by `action=scroll`.
        start_coordinate: (x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to start the drag from. Required only by `action=left_click_drag`.
        text: Required only by `action=type`, `action=key`, and `action=hold_key`. Can also be used by click or scroll actions to hold down keys while clicking or scrolling.
        
    Returns: tool results
    """

    # if use NOVA model, the image need to rescale
    rescale = True if os.environ.get("RESCALE") in [True,1,'1'] else False
    computer_tool = ComputerTool(ssh=ctx.request_context.lifespan_context.ssh,
                                 vnc=ctx.request_context.lifespan_context.vnc,
                                 is_nova = rescale
                                 )
    tool_input = dict(action=action, coordinate=coordinate, text=text,duration=duration,scroll_direction=scroll_direction,scroll_amount=scroll_amount)
    try:
        result = await computer_tool(**tool_input)
    except Exception as e:
        raise ValueError(f"{e}")
    
    if result.base64_image:
        return base64_to_pil(result.base64_image) 
    else:
        return {'output':result.output,"error":result.error}
    
@mcp.tool()
async def bash(ctx: Context, command: str,restart: bool = None):
    """
    Run commands in a bash shell
    * When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    * You have access to a mirror of common linux and python packages via apt and pip.
    * State is persistent across command calls and discussions with the user.
    * To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    * Please avoid commands that may produce a very large amount of output.
    * Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.
    
    Args: 
        command: the bash command to run. Required unless the tool is being restarted.
        restart: Specifying true will restart this tool. Otherwise, leave this unspecified.
    
    Returns: tool results
    """
    bash_tool = BashTool(ssh=ctx.request_context.lifespan_context.ssh)
    tool_input = dict(command=command, restart=restart)
    try:
        result = await bash_tool(**tool_input)
    except Exception as e:
        raise ValueError(f"{e}")
    return {'output':result.output,"error":result.error}

@mcp.tool()
async def str_replace_editor(ctx: Context,
                            command: Command,
                            path: str,
                            file_text: str | None = None,
                            view_range: list[int] | None = None,
                            old_str: str | None = None,
                            new_str: str | None = None,
                            insert_line: int | None = None):
    """
    Custom editing tool for viewing, creating and editing files
    * State is persistent across command calls and discussions with the user
    * If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
    * The `create` command cannot be used if the specified `path` already exists as a file
    * If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
    * The `undo_edit` command will revert the last edit made to the file at `path`

    Notes for using the `str_replace` command:
    * The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
    * If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
    * The `new_str` parameter should contain the edited lines that should replace the `old_str`
    
    Args:
        command: The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.
        path: Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.
        file_text: Required parameter of `create` command, with the content of the file to be created.
        view_range: Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.
        old_str: Required parameter of `str_replace` command containing the string in `path` to replace.
        new_str: Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.
        insert_line: Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.
    
    Returns: tool results
    """
    editor_tool = EditTool(ssh=ctx.request_context.lifespan_context.ssh)
    tool_input = dict(command=command, path=path,file_text=file_text, view_range=view_range, old_str=old_str, new_str=new_str, insert_line=insert_line )
    try:
        result = await editor_tool(**tool_input)
    except Exception as e:
        raise ValueError(f"{e}")
    return {'output':result.output,"error":result.error}

# Run server if executed directly
if __name__ == "__main__":
    mcp.run()