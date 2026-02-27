"""Tool for reading a skill's resource file."""

from typing import ClassVar

from langchain_core.tools import BaseTool

from langchain_agentskills.loaders.base import SkillLoader


class ReadSkillResourceTool(BaseTool):
    """Read a resource file from a skill."""

    name: str = "read_skill_resource"
    description: str = (
        "Read a resource file from a skill. "
        "Provide the skill name and the resource filename. "
        "Use load_skill first to see available resources."
    )

    loader: SkillLoader
    _not_serializable: ClassVar[bool] = True

    def _run(self, skill_name: str, resource_name: str) -> str:
        try:
            return self.loader.read_resource(skill_name, resource_name)
        except Exception as e:
            return f"Error reading resource '{resource_name}' from skill '{skill_name}': {e}"
