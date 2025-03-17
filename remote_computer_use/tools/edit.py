from collections import defaultdict
from typing import Literal, get_args

from anthropic.types.beta import BetaToolTextEditor20241022Param

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .tools_config import text_editor_description, text_editor_input_schema

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]
SNIPPET_LINES: int = 4


TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"
MAX_RESPONSE_LEN: int = 16000


def maybe_truncate(content: str, truncate_after: int | None = MAX_RESPONSE_LEN):
    """Truncate content and append a notice if content exceeds the specified length."""
    return (
        content
        if not truncate_after or len(content) <= truncate_after
        else content[:truncate_after] + TRUNCATED_MESSAGE
    )


class EditTool(BaseAnthropicTool):
    """
    A filesystem editor tool that allows the agent to view, create, and edit files via SSH.
    The tool parameters are defined by Anthropic and are not editable.
    """

    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    _file_history: dict[str, list[str]]
    _ssh_controller = None

    def __init__(self, ssh=None):
        """
        Initialize EditTool with an SSH controller
        
        Args:
            ssh_controller: An initialized SSHController instance
        """
        self._file_history = defaultdict(list)
        self._ssh_controller = ssh
        super().__init__()

    def to_params(self) -> BetaToolTextEditor20241022Param:
        return {
            "name": self.name,
            "type": self.api_type,
        }
    
    def to_params_nova(self):
        return {
            "toolSpec":{
                "name": self.name,
                "description": text_editor_description,
                "inputSchema": {"json": text_editor_input_schema}
            }
        }

    async def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ):
        if not self._ssh_controller:
            raise ToolError("SSH controller not initialized. Cannot perform file operations.")
        
        await self.validate_path(command, path)
        
        if command == "view":
            return await self.view(path, view_range)
        elif command == "create":
            if file_text is None:
                raise ToolError("Parameter `file_text` is required for command: create")
            await self.write_file(path, file_text)
            self._file_history[path].append(file_text)
            return ToolResult(output=f"File created successfully at: {path}")
        elif command == "str_replace":
            if old_str is None:
                raise ToolError(
                    "Parameter `old_str` is required for command: str_replace"
                )
            return await self.str_replace(path, old_str, new_str)
        elif command == "insert":
            if insert_line is None:
                raise ToolError(
                    "Parameter `insert_line` is required for command: insert"
                )
            if new_str is None:
                raise ToolError("Parameter `new_str` is required for command: insert")
            return await self.insert(path, insert_line, new_str)
        elif command == "undo_edit":
            return await self.undo_edit(path)
        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
        )

    async def validate_path(self, command: str, path: str):
        """
        Check that the path/command combination is valid through SSH.
        """
        # Check if it's an absolute path
        if not path.startswith("/"):
            suggested_path = "/" + path
            raise ToolError(
                f"The path {path} is not an absolute path, it should start with '/'. Maybe you meant {suggested_path}?"
            )

        # Check if path exists using SSH
        if command != "create":
            result = await self._ssh_controller.execute_command(f"[ -e '{path}' ] && echo 'exists' || echo 'not_exists'")
            if result["success"] and result["output"].strip() == "not_exists":
                raise ToolError(
                    f"The path {path} does not exist. Please provide a valid path."
                )
        
        if command == "create":
            result = await self._ssh_controller.execute_command(f"[ -e '{path}' ] && echo 'exists' || echo 'not_exists'")
            if result["success"] and result["output"].strip() == "exists":
                raise ToolError(
                    f"File already exists at: {path}. Cannot overwrite files using command `create`."
                )
        
        # Check if the path points to a directory
        if command != "view":
            result = await self._ssh_controller.execute_command(f"[ -d '{path}' ] && echo 'directory' || echo 'file'")
            if result["success"] and result["output"].strip() == "directory":
                raise ToolError(
                    f"The path {path} is a directory and only the `view` command can be used on directories"
                )


    async def view(self, path: str, view_range: list[int] | None = None):
        """Implement the view command via SSH"""
        # Check if path is a directory using SSH
        is_dir_result = await self._ssh_controller.execute_command(f"[ -d '{path}' ] && echo 'directory' || echo 'file'")
        is_directory = is_dir_result["success"] and "directory" in is_dir_result["output"]
        
        if is_directory:
            if view_range:
                raise ToolError(
                    "The `view_range` parameter is not allowed when `path` points to a directory."
                )

            find_result = await self._ssh_controller.execute_command(f"find {path} -maxdepth 2 -not -path '*/\\.*'")
            if not find_result["success"]:
                return CLIResult(output="", error=find_result["error"])
            
            stdout = f"Here's the files and directories up to 2 levels deep in {path}, excluding hidden items:\n{find_result['output']}\n"
            return CLIResult(output=stdout, error="")

        file_content = await self.read_file(path)
        init_line = 1
        if view_range:
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                raise ToolError(
                    "Invalid `view_range`. It should be a list of two integers."
                )
            file_lines = file_content.split("\n")
            n_lines_file = len(file_lines)
            init_line, final_line = view_range
            if init_line < 1 or init_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                )
            if final_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                )
            if final_line != -1 and final_line < init_line:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"
                )

            if final_line == -1:
                file_content = "\n".join(file_lines[init_line - 1:])
            else:
                file_content = "\n".join(file_lines[init_line - 1: final_line])

        return CLIResult(
            output=self._make_output(file_content, str(path), init_line=init_line)
        )

    async def str_replace(self, path: str, old_str: str, new_str: str | None):
        """Implement the str_replace command via SSH"""
        # Read the file content
        file_content = await self.read_file(path)
        file_content = file_content.expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ""

        # Check if old_str is unique in the file
        occurrences = file_content.count(old_str)
        if occurrences == 0:
            raise ToolError(
                f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}."
            )
        elif occurrences > 1:
            file_content_lines = file_content.split("\n")
            lines = [
                idx + 1
                for idx, line in enumerate(file_content_lines)
                if old_str in line
            ]
            raise ToolError(
                f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique"
            )

        # Replace old_str with new_str
        new_file_content = file_content.replace(old_str, new_str)

        # Write the new content to the file
        await self.write_file(path, new_file_content)

        # Save the content to history
        self._file_history[path].append(file_content)

        # Create a snippet of the edited section
        replacement_line = file_content.split(old_str)[0].count("\n")
        start_line = max(0, replacement_line - SNIPPET_LINES)
        end_line = replacement_line + SNIPPET_LINES + new_str.count("\n")
        snippet = "\n".join(new_file_content.split("\n")[start_line : end_line + 1])

        # Prepare the success message
        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet, f"a snippet of {path}", start_line + 1
        )
        success_msg += "Review the changes and make sure they are as expected. Edit the file again if necessary."

        return CLIResult(output=success_msg)

    async def insert(self, path: str, insert_line: int, new_str: str):
        """Implement the insert command via SSH"""
        file_text = await self.read_file(path)
        file_text = file_text.expandtabs()
        new_str = new_str.expandtabs()
        file_text_lines = file_text.split("\n")
        n_lines_file = len(file_text_lines)

        if insert_line < 0 or insert_line > n_lines_file:
            raise ToolError(
                f"Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, n_lines_file]}"
            )

        new_str_lines = new_str.split("\n")
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - SNIPPET_LINES) : insert_line]
            + new_str_lines
            + file_text_lines[insert_line : insert_line + SNIPPET_LINES]
        )

        new_file_text = "\n".join(new_file_text_lines)
        snippet = "\n".join(snippet_lines)

        await self.write_file(path, new_file_text)
        self._file_history[path].append(file_text)

        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet,
            "a snippet of the edited file",
            max(1, insert_line - SNIPPET_LINES + 1),
        )
        success_msg += "Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
        return CLIResult(output=success_msg)

    async def undo_edit(self, path: str):
        """Implement the undo_edit command via SSH"""
        if not self._file_history[path]:
            raise ToolError(f"No edit history found for {path}.")

        old_text = self._file_history[path].pop()
        await self.write_file(path, old_text)

        return CLIResult(
            output=f"Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}"
        )

    async def read_file(self, path: str):
        """Read file content via SSH"""
        try:
            result = await self._ssh_controller.execute_command(f"cat '{path}'")
            if not result["success"]:
                raise ToolError(f"Failed to read {path}: {result['error']}")
            return result["output"]
        except Exception as e:
            raise ToolError(f"Ran into {e} while trying to read {path}") from None

    async def write_file(self, path: str, file_content: str):
        """Write file content via SSH, creating parent directories if needed"""
        try:
            # Extract the directory part of the path
            directory = path.rsplit('/', 1)[0]
            if not directory:
                directory = "/"
                
            # Create the directory if it doesn't exist (mkdir -p creates all necessary parent directories)
            mkdir_result = await self._ssh_controller.execute_command(f"mkdir -p '{directory}'")
            if not mkdir_result["success"]:
                raise ToolError(f"Failed to create directory {directory}: {mkdir_result['error']}")
            
            # Create a temporary file with the content
            temp_path = f"/tmp/edit_tool_{hash(path)}_{hash(file_content) % 10000}"
            
            # Use heredoc to safely write the file content
            echo_command = f"cat > '{temp_path}' << 'EOFMARKER'\n{file_content}\nEOFMARKER"
            result = await self._ssh_controller.execute_command(echo_command)
            
            if not result["success"]:
                raise ToolError(f"Failed to create temporary file: {result['error']}")
                
            # Move the temporary file to the target path
            move_result = await self._ssh_controller.execute_command(f"mv '{temp_path}' '{path}'")
            
            if not move_result["success"]:
                raise ToolError(f"Failed to write to {path}: {move_result['error']}")
        except Exception as e:
            raise ToolError(f"Ran into {e} while trying to write to {path}") from None


    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ):
        """Generate output for the CLI based on the content of a file."""
        file_content = maybe_truncate(file_content)
        if expand_tabs:
            file_content = file_content.expandtabs()
        file_content = "\n".join(
            [
                f"{i + init_line:6}\t{line}"
                for i, line in enumerate(file_content.split("\n"))
            ]
        )
        return (
            f"Here's the result of running `cat -n` on {file_descriptor}:\n"
            + file_content
            + "\n"
        )
