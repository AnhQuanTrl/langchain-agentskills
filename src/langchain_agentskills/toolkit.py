"""SkillsToolkit — main entry point for using skills with LangChain agents."""

from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import model_validator

from langchain_agentskills.executor import ScriptExecutor
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.loaders.composite import CompositeSkillLoader
from langchain_agentskills.loaders.directory import DirectorySkillLoader
from langchain_agentskills.tools.list_skills import ListSkillsTool
from langchain_agentskills.tools.load_skill import LoadSkillTool
from langchain_agentskills.tools.read_resource import ReadSkillResourceTool
from langchain_agentskills.tools.run_script import RunSkillScriptTool

# We import BaseToolkit conditionally — it was added in langchain-core 0.3
try:
    from langchain_core.tools import BaseToolkit
except ImportError:
    # Fallback for older langchain-core versions
    from pydantic import BaseModel as BaseToolkit  # type: ignore[assignment]

_ALL_TOOLS = frozenset({
    "list_skills",
    "load_skill",
    "read_skill_resource",
    "run_skill_script",
})


class SkillsToolkit(BaseToolkit):  # type: ignore[misc]
    """Toolkit that provides LangChain tools for interacting with skills.

    Examples:
        Local skills only::

            toolkit = SkillsToolkit(directories=["./skills"])
            tools = toolkit.get_tools()

        Custom loader::

            toolkit = SkillsToolkit(loaders=[MyGitHubLoader(repo="org/skills")])

        Combined (local takes priority)::

            toolkit = SkillsToolkit(
                directories=["./skills"],
                loaders=[MyGitHubLoader(...)],
            )
    """

    directories: list[str] = []
    loaders: list[Any] = []
    exclude_tools: set[str] = set()
    script_timeout: int = 30

    _resolved_loader: SkillLoader | None = None
    _executor: ScriptExecutor | None = None

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="after")
    def _build_loader(self) -> "SkillsToolkit":
        all_loaders: list[SkillLoader] = []

        # Directory loaders first (higher priority)
        for d in self.directories:
            all_loaders.append(DirectorySkillLoader(Path(d)))

        # Then custom loaders
        for loader in self.loaders:
            if not isinstance(loader, SkillLoader):
                raise TypeError(
                    f"Expected SkillLoader, got {type(loader).__name__}"
                )
            all_loaders.append(loader)

        if not all_loaders:
            raise ValueError(
                "SkillsToolkit requires at least one directory or loader"
            )

        if len(all_loaders) == 1:
            self._resolved_loader = all_loaders[0]
        else:
            self._resolved_loader = CompositeSkillLoader(all_loaders)

        self._executor = ScriptExecutor(timeout=self.script_timeout)

        # Validate exclude_tools
        invalid = self.exclude_tools - _ALL_TOOLS
        if invalid:
            raise ValueError(f"Unknown tool names in exclude_tools: {invalid}")

        return self

    def get_instructions(self) -> str:
        """Return a markdown summary of all available skills.

        Designed to be injected into the agent's system prompt so it
        already knows what skills exist without calling ``list_skills``.
        """
        loader = self._resolved_loader
        assert loader is not None

        skills = loader.list_skills()
        if not skills:
            return "No skills available."

        lines = ["# Available Skills", ""]
        for s in skills:
            lines.append(f"- **{s.name}**: {s.description}")
        lines.append("")
        lines.append(
            "Use `load_skill` to get full instructions for a skill, "
            "`read_skill_resource` to read its resources, "
            "and `run_skill_script` to execute its scripts."
        )
        return "\n".join(lines)

    def get_tools(self) -> list[BaseTool]:
        """Return the list of LangChain tools, minus any excluded ones."""
        loader = self._resolved_loader
        executor = self._executor
        assert loader is not None
        assert executor is not None

        tool_map: dict[str, BaseTool] = {
            "list_skills": ListSkillsTool(loader=loader),
            "load_skill": LoadSkillTool(loader=loader),
            "read_skill_resource": ReadSkillResourceTool(loader=loader),
            "run_skill_script": RunSkillScriptTool(loader=loader, executor=executor),
        }

        return [
            tool for name, tool in tool_map.items()
            if name not in self.exclude_tools
        ]
