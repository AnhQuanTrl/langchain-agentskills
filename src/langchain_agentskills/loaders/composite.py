"""Composite loader that merges multiple skill loaders with priority ordering."""

from pathlib import Path

from langchain_agentskills.exceptions import SkillNotFoundError
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.models import SkillContent, SkillMetadata


class CompositeSkillLoader(SkillLoader):
    """Merge multiple loaders with priority ordering.

    The first loader in the list has highest priority — if multiple loaders
    have a skill with the same name, the first one wins.

    Args:
        loaders: Ordered list of skill loaders (first = highest priority).
    """

    def __init__(self, loaders: list[SkillLoader]) -> None:
        if not loaders:
            raise ValueError("CompositeSkillLoader requires at least one loader")
        self._loaders = loaders

    def list_skills(self) -> list[SkillMetadata]:
        seen: set[str] = set()
        skills: list[SkillMetadata] = []
        for loader in self._loaders:
            for skill in loader.list_skills():
                if skill.name not in seen:
                    seen.add(skill.name)
                    skills.append(skill)
        return skills

    def load_skill(self, name: str) -> SkillContent:
        loader = self._find_loader(name)
        return loader.load_skill(name)

    def read_resource(self, skill_name: str, resource_name: str) -> str:
        loader = self._find_loader(skill_name)
        return loader.read_resource(skill_name, resource_name)

    def has_skill(self, name: str) -> bool:
        return any(loader.has_skill(name) for loader in self._loaders)

    def read_script(self, skill_name: str, script_name: str) -> Path:
        loader = self._find_loader(skill_name)
        return loader.read_script(skill_name, script_name)

    def _find_loader(self, name: str) -> SkillLoader:
        """Find the first loader that has the named skill."""
        for loader in self._loaders:
            if loader.has_skill(name):
                return loader
        raise SkillNotFoundError(name)
