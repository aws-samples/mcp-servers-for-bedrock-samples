import asyncio
import os
from typing import ClassVar, Literal

from anthropic.types.beta import BetaToolBash20241022Param

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .tools_config import bash_description,bash_input_schema


class _BashSession:
    """A session of a bash shell over SSH."""

    _started: bool
    _ssh_controller: 'SSHController'

    command: str = "/bin/bash"
    _timeout: float = 120.0  # seconds

    def __init__(self, ssh_controller):
        self._started = False
        self._timed_out = False
        self._ssh_controller = ssh_controller

    async def start(self):
        if self._started:
            return

        # Check if SSH controller is connected
        if not self._ssh_controller.client:
            success = await self._ssh_controller.connect()
            if not success:
                raise ToolError("Failed to connect to SSH server")
        
        self._started = True

    def stop(self):
        """No need to terminate the bash shell in SSH mode."""
        if not self._started:
            raise ToolError("Session has not started.")
        # In SSH mode, we don't terminate anything
        # The SSH connection is managed by SSHController
        pass

    async def run(self, command: str):
        """Execute a command via SSH."""
        if not self._started:
            raise ToolError("Session has not started.")
        
        if self._timed_out:
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            )

        try:
            # Execute the command via SSH with a timeout
            async with asyncio.timeout(self._timeout):
                result = await self._ssh_controller.execute_command(command)
        except asyncio.TimeoutError:
            self._timed_out = True
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        # Handle SSH connection failures or command errors
        if not result["success"]:
            if "error" in result and "Connection" in result["error"]:
                # SSH connection likely dropped
                self._started = False
                return CLIResult(output="", error=f"SSH connection error: {result.get('error', '')}")
            return CLIResult(output="", error=result.get("error", "Unknown SSH error"))
        
        output = result.get("output", "")
        error = result.get("error", "")
        
        # Follow the original behavior of trimming trailing newlines
        if output.endswith("\n"):
            output = output[:-1]
        
        if error and error.endswith("\n"):
            error = error[:-1]
        
        return CLIResult(output=output, error=error)


class BashTool(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands.
    The tool parameters are defined by Anthropic and are not editable.
    """

    _session: _BashSession | None
    name: ClassVar[Literal["bash"]] = "bash"
    api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"
    ssh = None
    
    def __init__(self,ssh):
        self._session = None
        self.ssh = ssh
        super().__init__()

    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession(ssh_controller=self.ssh)
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            self._session = _BashSession(ssh_controller=self.ssh)
            await self._session.start()

        if command is not None:
            return await self._session.run(command)

        raise ToolError("no command provided.")

    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }
    
    def to_params_nova(self):
        return {
            "toolSpec":{
                "name":self.name,
                "description":bash_description,
                "inputSchema":{"json":bash_input_schema}
            }
        }