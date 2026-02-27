"""Tool for listing available skills."""

from typing import ClassVar

from langchain_core.tools import BaseTool

from langchain_agentskills.loaders.base import SkillLoader


class ListSkillsTool(BaseTool):
    """List all available skills with their names and descriptions."""

    name: str = "list_skills"
    description: str = (
        "List all available skills. Returns skill names and descriptions. "
        "Use this to discover what skills are available before loading one."
    )

    loader: SkillLoader
    _not_serializable: ClassVar[bool] = True

    def _run(self) -> str:
        try:
            skills = self.loader.list_skills()
        except Exception as e:
            return f"Error listing skills: {e}"

        if not skills:
            return "No skills available."

        lines = []
        for s in skills:
            lines.append(f"- **{s.name}**: {s.description}")
        return "\n".join(lines)
