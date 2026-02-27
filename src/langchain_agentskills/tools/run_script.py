"""Tool for running a skill's script."""

from typing import ClassVar

from langchain_core.tools import BaseTool

from langchain_agentskills.executor import ScriptExecutor
from langchain_agentskills.loaders.base import SkillLoader


class RunSkillScriptTool(BaseTool):
    """Execute a script provided by a skill."""

    name: str = "run_skill_script"
    description: str = (
        "Run a script from a skill. "
        "Provide the skill name, script filename, and optional arguments. "
        "Use load_skill first to see available scripts."
    )

    loader: SkillLoader
    executor: ScriptExecutor
    _not_serializable: ClassVar[bool] = True

    def _run(
        self,
        skill_name: str,
        script_name: str,
        script_args: list[str] | None = None,
    ) -> str:
        try:
            script_path = self.loader.read_script(skill_name, script_name)
            return self.executor.run(script_path, script_args)
        except Exception as e:
            return f"Error running script '{script_name}' from skill '{skill_name}': {e}"
