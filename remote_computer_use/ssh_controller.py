"""
SSH Controller Module for Computer Use MCP Server
Handles SSH connections and xdotool command execution
"""
import asyncio
import paramiko
import os


class SSHController:
    def __init__(self, host, port, username, password,pem_file,display_num=1):
        """
        Initialize SSH controller with connection parameters
        
        Args:
            host (str): SSH server hostname or IP
            port (int): SSH server port
            username (str): SSH username
            password (str): SSH password
            pem_file (str): ec2 pem files
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.pem_file = pem_file
        self.display_num = display_num
        self.client = None
        
    async def connect(self):
        """
        Establish SSH connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Use asyncio to run the blocking SSH connection in a thread pool
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.pem_file:
                private_key = paramiko.RSAKey.from_private_key_file(self.pem_file)  
                await asyncio.to_thread(
                    self.client.connect,
                    self.host, 
                    port=self.port, 
                    username=self.username, 
                    password=self.password,
                    pkey=private_key
                )
            else:
                await asyncio.to_thread(
                    self.client.connect,
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            return True
        except Exception as e:
            print(f"SSH connection error: {e}")
            return False
        
    async def disconnect(self):
        """Close SSH connection"""
        if self.client:
            try:
                await asyncio.to_thread(self.client.close)
            except Exception as e:
                print(f"SSH disconnect error: {e}")
            finally:
                self.client = None
            
    async def execute_command(self, command):
        """
        Execute command on remote server
        
        Args:
            command (str): Command to execute
            
        Returns:
            dict: Command execution result
        """
        if not self.client:
            success = await self.connect()
            if not success:
                return {"success": False, "error": "Failed to connect to SSH server"}
            
        try:
            # Execute command and get output
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, command)
            output = await asyncio.to_thread(stdout.read)
            error = await asyncio.to_thread(stderr.read)
            
            output = output.decode() if output else ""
            error = error.decode() if error else ""
            
            if error:
                return {"success": False, "error": error, "output": output}
            return {"success": True, "output": output}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def launch_application(self, app_name):
        """
        Launch application using xdotool
        
        Args:
            app_name (str): Application name
            
        Returns:
            dict: Command execution result
        """
        # Try to activate existing window or launch new instance
        command = f"DISPLAY=:{self.display_num} xdotool search --name '{app_name}' windowactivate || DISPLAY=:{self.display_num} {app_name} &"
        return await self.execute_command(command)
        
    async def window_management(self, window_id, action):
        """
        Manage window (maximize, minimize, etc.)
        
        Args:
            window_id (str): Window ID or name
            action (str): Action to perform (maximize, minimize, etc.)
            
        Returns:
            dict: Command execution result
        """
        # Activate window and perform action
        command = f"DISPLAY=:{self.display_num} xdotool windowactivate {window_id} && DISPLAY=:{self.display_num} xdotool {action}"
        return await self.execute_command(command)
    
    async def list_windows(self):
        """
        List all windows
        
        Returns:
            dict: Command execution result with window list
        """
        command = f"DISPLAY=:{self.display_num} xdotool search --all --onlyvisible --name ''"
        result = await self.execute_command(command)
        
        if result["success"]:
            # Get window names for each window ID
            window_ids = result["output"].strip().split("\n")
            windows = []
            
            for window_id in window_ids:
                if window_id:
                    name_cmd = f"DISPLAY=:{self.display_num} xdotool getwindowname {window_id}"
                    name_result = await self.execute_command(name_cmd)
                    
                    if name_result["success"]:
                        windows.append({
                            "id": window_id,
                            "name": name_result["output"].strip()
                        })
            
            result["windows"] = windows
            
        return result
    
    async def get_window_info(self, window_id):
        """
        Get window information
        
        Args:
            window_id (str): Window ID
            
        Returns:
            dict: Window information
        """
        # Get window geometry
        geometry_cmd = f"DISPLAY=:{self.display_num} xdotool getwindowgeometry {window_id}"
        geometry_result = await self.execute_command(geometry_cmd)
        
        # Get window name
        name_cmd = f"DISPLAY=:{self.display_num} xdotool getwindowname {window_id}"
        name_result = await self.execute_command(name_cmd)
        
        return {
            "success": geometry_result["success"] and name_result["success"],
            "id": window_id,
            "name": name_result.get("output", "").strip() if name_result["success"] else "",
            "geometry": geometry_result.get("output", "") if geometry_result["success"] else ""
        }
