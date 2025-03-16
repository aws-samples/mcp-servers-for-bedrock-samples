"""
VNC Controller Module for Computer Use MCP Server
Handles VNC connections, screen capture, and input events
"""
import asyncio
from vncdotool import api
import io
from PIL import Image
import tempfile


class VNCController:
    def __init__(self, host, port, username, password):
        """
        Initialize VNC controller with connection parameters
        
        Args:
            host (str): VNC server hostname or IP
            port (int): VNC server port
            username (str): VNC username
            password (str): VNC password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        
    async def connect(self):
        """
        Establish VNC connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Use asyncio to run the blocking VNC connection in a thread pool
            self.client = await asyncio.to_thread(
                api.connect, 
                f"{self.host}::{self.port}", 
                self.password
            )
            return True
        except Exception as e:
            print(f"VNC connection error: {e}")
            return False
        
    async def disconnect(self):
        """Close VNC connection"""
        if self.client:
            try:
                await asyncio.to_thread(self.client.disconnect)
            except Exception as e:
                print(f"VNC disconnect error: {e}")
            finally:
                self.client = None
            
    async def capture_screenshot(self):
        """
        Capture screenshot from VNC session
        
        Returns:
            PIL.Image: Screenshot image
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        
        try:
            # Capture screen and convert to PIL Image using temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tmp:
                await asyncio.to_thread(self.client.captureScreen, tmp.name)
                image = Image.open(tmp.name)
                return image
        except Exception as e:
            raise Exception(f"Screenshot capture error: {e}")
            
        
    async def capture_region(self,x: int, y: int, w: int, h: int, incremental: bool = False):
        """
        Save a region of the current display to filename
        
        Returns:
            PIL.Image: Screenshot image
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        
        try:
            # Capture screen and convert to PIL Image using temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tmp:
                await asyncio.to_thread(self.client.captureRegion, tmp.name,x,y,w,h,incremental)
                image = Image.open(tmp.name)
                return image
        except Exception as e:
            raise Exception(f"Region Screenshot capture error: {e}")
            
        
    async def mouse_move(self, x, y):
        """
        Move mouse to coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        try:
            await asyncio.to_thread(self.client.mouseMove, x, y)
        except Exception as e:
            raise Exception(f"Mouse move error: {e}")
            
        
    async def mouse_click(self, x, y, button=1):
        """
        Click at coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            button (int): Mouse button (1=left, 2=middle, 3=right)
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        try:
            await asyncio.to_thread(self.client.mousePress, button)
            await asyncio.to_thread(self.client.mouseUp, button)
            await asyncio.to_thread(self.client.mouseUp, button)
        except Exception as e:
            raise Exception(f"Mouse click error: {e}")
            
    
    async def mouse_scroll(self, steps=1, direction="down"):
        """
        Scroll the mouse wheel
        
        Args:
            steps (int): Number of scroll steps
            direction (str): 'up' or 'down'
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        
        button = 4 if direction == "up" else 5  # 4 = scroll up, 5 = scroll down
        
        for _ in range(steps):
            try:
                await asyncio.to_thread(self.client.mousePress, button)
                await asyncio.to_thread(self.client.mouseDown, button)
            except Exception as e:
                raise Exception(f"Mouse scroll error: {e}")
        
    async def type_text(self, text):
        """
        Type text
        
        Args:
            text (str): Text to type
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
            
        async def send_text(text):
            for char in text:
                self.client.keyPress(char)
        
        try:
            await asyncio.to_thread(send_text, text)
        except Exception as e:
            raise Exception(f"Text input error: {e}")
    
    async def key_press(self, key):
        """
        Press a key
        
        Args:
            key (str): Key to press (e.g., 'enter', 'escape', etc.)
        """
        if not self.client:
            success = await self.connect()
            if not success:
                raise Exception("Failed to connect to VNC server")
        
        try:
            await asyncio.to_thread(self.client.keyPress, key)
        except Exception as e:
            raise Exception(f"Key press error: {e}")
