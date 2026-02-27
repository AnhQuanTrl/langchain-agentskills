"""Exceptions for langchain-agentskills."""


class SkillException(Exception):
    """Base exception for skill operations."""


class SkillNotFoundError(SkillException):
    """Raised when a requested skill cannot be found."""

    def __init__(self, skill_name: str) -> None:
        self.skill_name = skill_name
        super().__init__(f"Skill not found: {skill_name}")


class SkillValidationError(SkillException):
    """Raised when a skill fails validation."""


class SkillResourceNotFoundError(SkillException):
    """Raised when a requested resource cannot be found within a skill."""

    def __init__(self, skill_name: str, resource_name: str) -> None:
        self.skill_name = skill_name
        self.resource_name = resource_name
        super().__init__(
            f"Resource '{resource_name}' not found in skill '{skill_name}'"
        )


class SkillScriptExecutionError(SkillException):
    """Raised when a skill script fails to execute."""


class SkillLoaderError(SkillException):
    """Raised when a loader encounters an error."""
