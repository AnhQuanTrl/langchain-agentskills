"""Standalone script executor — runs scripts locally regardless of loader origin."""

import os
import subprocess
from pathlib import Path

from langchain_agentskills.exceptions import SkillScriptExecutionError

_DEFAULT_SCRIPT_TIMEOUT = 30  # seconds


class ScriptExecutor:
    """Execute skill scripts locally.

    Takes a path to a script on disk and runs it via subprocess.

    Args:
        timeout: Max seconds for script execution. Defaults to 30.
    """

    def __init__(self, timeout: int = _DEFAULT_SCRIPT_TIMEOUT) -> None:
        self._timeout = timeout

    def run(
        self,
        script_path: Path,
        args: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """Execute a script and return its stdout.

        Args:
            script_path: Path to the script file on disk.
            args: Optional command-line arguments.
            timeout: Override the default timeout for this execution.

        Returns:
            The script's stdout as a string.

        Raises:
            SkillScriptExecutionError: If the script fails or times out.
        """
        effective_timeout = timeout if timeout is not None else self._timeout
        script_name = script_path.name

        if not script_path.is_file():
            raise SkillScriptExecutionError(
                f"Script not found: {script_path}"
            )

        if not os.access(script_path, os.X_OK):
            raise SkillScriptExecutionError(
                f"Script '{script_name}' is not executable"
            )

        cmd = [str(script_path)]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(script_path.parent),
            )
        except subprocess.TimeoutExpired:
            raise SkillScriptExecutionError(
                f"Script '{script_name}' timed out after {effective_timeout}s"
            )
        except OSError as e:
            raise SkillScriptExecutionError(
                f"Failed to execute script '{script_name}': {e}"
            )

        output = result.stdout
        if result.returncode != 0:
            output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
            raise SkillScriptExecutionError(
                f"Script '{script_name}' exited with code {result.returncode}:\n{output}"
            )

        return output
