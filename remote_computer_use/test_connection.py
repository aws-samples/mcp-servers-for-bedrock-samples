#!/usr/bin/env python3
"""
Test script for VNC and SSH connections
Use this to verify your connection settings before running the MCP server
"""
import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
import paramiko
from vncdotool import api
import io
from PIL import Image
from vnc_controller import VNCController
from ssh_controller import SSHController


def print_success(message):
    """Print success message in green"""
    print(f"\033[92m✓ {message}\033[0m")

def print_error(message):
    """Print error message in red"""
    print(f"\033[91m✗ {message}\033[0m")

def print_info(message):
    """Print info message in blue"""
    print(f"\033[94m• {message}\033[0m")

async def test_vnc_controller(host, port, username, password):
    """Test VNC controller"""
    vnc_controller = VNCController(host, port, username, password)
    vnc_success = await vnc_controller.connect()
    if not vnc_success:
        print_error("Warning: Failed to connect to VNC server on startup")
    print_success("VNC Controller connected successfully")
    image = await vnc_controller.capture_screenshot()
    if image :
        print_success("VNC Controller captured screenshot successfully")
    else:
        vnc_success = False
        
    await vnc_controller.mouse_click(327,91,1)
    return vnc_success
    
        
    
        
async def test_ssh_connection(host, port, username, password,pem_file):
    """Test SSH connection and xdotool availability"""
    print_info(f"Testing SSH connection to {host}:{port}...")
    ssh_controller = SSHController(host, port, username, password, pem_file)
    ssh_success = await ssh_controller.connect()
    if not ssh_success:
        print_error("Warning: Failed to connect to SSH server on startup")
    print_success("SSH Controller connected successfully")
    
    # Check if xdotool is installed
    print_info("Checking if xdotool is installed...")
    results = await ssh_controller.execute_command("which xdotool")
    stdout = results.get('output')
    xdotool_path = stdout.strip()
    if xdotool_path:
        print_success(f"xdotool found at {xdotool_path}")
        
        # Test xdotool with DISPLAY
        print_info("Testing xdotool with DISPLAY environment variable...")
        results = await ssh_controller.execute_command("DISPLAY=:1 xdotool getmouselocation")
        stderr = results.get('error')
        output = results.get('output')
        if stderr:
            print_error(f"xdotool test failed: {stderr}")
            print_info("You may need to run 'xhost +' on the remote machine")
            ssh_success = False
        else:
            print_success(f"xdotool test successful: {output}")
    else:
        print_error("xdotool not found. Please install it with: sudo apt install xdotool")
        ssh_success = False
    
    await ssh_controller.disconnect()
    
    print_success("SSH connection closed")
    return ssh_success
        


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test VNC and SSH connections")
    parser.add_argument("--env", help="Path to .env file", default=".env")
    parser.add_argument("--vnc-only", action="store_true", help="Test only VNC connection")
    parser.add_argument("--ssh-only", action="store_true", help="Test only SSH connection")
    args = parser.parse_args()
    
    # Load environment variables from .env file
    if os.path.exists(args.env):
        load_dotenv(args.env)
        print_info(f"Loaded environment variables from {args.env}")
    else:
        print_info("No .env file found, using environment variables")
    
    # Get connection details
    vnc_host = os.environ.get("VNC_HOST")
    vnc_port = int(os.environ.get("VNC_PORT", "5900"))
    vnc_username = os.environ.get("VNC_USERNAME")
    vnc_password = os.environ.get("VNC_PASSWORD")
    ssh_port = int(os.environ.get("SSH_PORT", "22"))
    pem_file = os.environ.get("PEM_FILE", "")
    
    # Validate required environment variables
    if not vnc_host:
        print_error("VNC_HOST environment variable is required")
        return False
    if not vnc_password:
        print_error("VNC_PASSWORD environment variable is required")
        return False
    if not vnc_username:
        print_error("VNC_USERNAME environment variable is required")
        return False
    
    print_info(f"Testing connection to {vnc_host}")
    success = True
    
    # Test VNC connection
    if not args.ssh_only:
        vnc_success = await test_vnc_controller(vnc_host, vnc_port, vnc_username, vnc_password)
        success = success and vnc_success
    
    # Test SSH connection
    if not args.vnc_only:
        ssh_success = await test_ssh_connection(vnc_host, ssh_port, vnc_username, vnc_password,pem_file)
        success = success and ssh_success
    
    # Print summary
    print("\n" + "=" * 50)
    if success:
        print_success("All tests completed successfully!")
        print_info("You can now run the Computer Use MCP Server")
    else:
        print_error("Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
