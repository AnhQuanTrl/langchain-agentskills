"""Skill middleware for LangChain agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from langchain_core.messages import AIMessage, SystemMessage

from langchain_agentskills.executor import ScriptExecutor
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.tools.load_skill import LoadSkillTool
from langchain_agentskills.tools.read_resource import ReadSkillResourceTool
from langchain_agentskills.tools.run_script import RunSkillScriptTool

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from langchain.agents.middleware.types import (
        ModelRequest,
        ModelResponse,
        ResponseT,
    )
    from langgraph.typing import ContextT

from langchain.agents.middleware.types import AgentMiddleware


class SkillMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions and provides skill tools.

    Registers ``load_skill``, ``read_skill_resource``, and ``run_skill_script``
    tools, and injects a summary of available skills into the system prompt so
    the agent knows what skills exist without an extra tool call.

    Args:
        loader: The skill loader to use.
        executor: Script executor for running skill scripts. If not provided,
            a default executor with 30s timeout is created.
        exclude_tools: Tool names to exclude (e.g. ``{"run_skill_script"}``).

    Example:
        ```python
        from langchain.agents import create_agent
        from langchain_agentskills import SkillMiddleware, DirectorySkillLoader

        loader = DirectorySkillLoader("./skills")
        agent = create_agent(
            "anthropic:claude-sonnet-4-20250514",
            middleware=[SkillMiddleware(loader=loader)],
        )
        ```
    """

    def __init__(
        self,
        loader: SkillLoader,
        *,
        executor: ScriptExecutor | None = None,
        exclude_tools: set[str] | None = None,
    ) -> None:
        super().__init__()
        self._loader = loader
        self._executor = executor or ScriptExecutor()
        exclude = exclude_tools or set()

        # Build the skills prompt from available skills
        skills = loader.list_skills()
        if skills:
            lines = [f"- **{s.name}**: {s.description}" for s in skills]
            self._skills_prompt = "\n".join(lines)
        else:
            self._skills_prompt = "No skills available."

        # Register tools
        all_tools = {
            "load_skill": LoadSkillTool(loader=loader),
            "read_skill_resource": ReadSkillResourceTool(loader=loader),
            "run_skill_script": RunSkillScriptTool(
                loader=loader, executor=self._executor
            ),
        }
        self.tools = [t for name, t in all_tools.items() if name not in exclude]

    def _build_system_message(
        self, existing: SystemMessage | None
    ) -> SystemMessage:
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self._skills_prompt}\n\n"
            "Use the `load_skill` tool when you need detailed instructions "
            "for handling a specific type of request."
        )
        if existing is not None:
            new_content = [
                *existing.content_blocks,
                {"type": "text", "text": skills_addendum},
            ]
        else:
            new_content = [{"type": "text", "text": skills_addendum}]
        return SystemMessage(
            content=cast("list[str | dict[str, str]]", new_content)
        )

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT] | AIMessage:
        """Inject skill descriptions into the system prompt."""
        new_system = self._build_system_message(request.system_message)
        return handler(request.override(system_message=new_system))

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[
            [ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]
        ],
    ) -> ModelResponse[ResponseT] | AIMessage:
        """Async: inject skill descriptions into the system prompt."""
        new_system = self._build_system_message(request.system_message)
        return await handler(request.override(system_message=new_system))
