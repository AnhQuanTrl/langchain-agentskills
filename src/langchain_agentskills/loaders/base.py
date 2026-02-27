"""Abstract base class for skill loaders."""

from abc import ABC, abstractmethod
from pathlib import Path

from langchain_agentskills.models import SkillContent, SkillMetadata


class SkillLoader(ABC):
    """Abstract base for loading skills from any source.

    Subclass this to add new skill sources (e.g., GitHub, S3, database).
    """

    @abstractmethod
    def list_skills(self) -> list[SkillMetadata]:
        """Return metadata for all available skills."""

    @abstractmethod
    def load_skill(self, name: str) -> SkillContent:
        """Load the full content of a skill by name.

        Raises:
            SkillNotFoundError: If the skill does not exist.
        """

    @abstractmethod
    def read_resource(self, skill_name: str, resource_name: str) -> str:
        """Read a resource file from a skill.

        Raises:
            SkillNotFoundError: If the skill does not exist.
            SkillResourceNotFoundError: If the resource does not exist.
        """

    @abstractmethod
    def has_skill(self, name: str) -> bool:
        """Check if a skill exists in this loader."""

    @abstractmethod
    def read_script(self, skill_name: str, script_name: str) -> Path:
        """Return the local path to a script file from a skill.

        Raises:
            SkillNotFoundError: If the skill does not exist.
            SkillResourceNotFoundError: If the script does not exist.
        """
