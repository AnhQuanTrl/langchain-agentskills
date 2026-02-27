"""Tool for loading a skill's full instructions."""

from typing import ClassVar

from langchain_core.tools import BaseTool

from langchain_agentskills.loaders.base import SkillLoader


class LoadSkillTool(BaseTool):
    """Load a skill's full instructions, resources, and scripts."""

    name: str = "load_skill"
    description: str = (
        "Load a skill by name to get its full instructions. "
        "Returns the skill's markdown body, available resources, and scripts. "
        "Use list_skills first to discover available skill names."
    )

    loader: SkillLoader
    _not_serializable: ClassVar[bool] = True

    def _run(self, skill_name: str) -> str:
        try:
            skill = self.loader.load_skill(skill_name)
        except Exception as e:
            return f"Error loading skill '{skill_name}': {e}"

        parts = [skill.body]

        if skill.resources:
            parts.append(
                "\n\n**Available resources** "
                "(use read_skill_resource to read):\n"
                + "\n".join(f"- {r}" for r in skill.resources)
            )

        if skill.scripts:
            parts.append(
                "\n\n**Available scripts** "
                "(use run_skill_script to execute):\n"
                + "\n".join(f"- {s}" for s in skill.scripts)
            )

        return "".join(parts)
