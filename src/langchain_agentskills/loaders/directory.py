"""Load skills from a local directory."""

from pathlib import Path

from langchain_agentskills.exceptions import (
    SkillLoaderError,
    SkillNotFoundError,
    SkillResourceNotFoundError,
    SkillValidationError,
)
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.models import SkillContent, SkillMetadata
from langchain_agentskills.parsing import frontmatter_to_metadata, parse_skill_md

_SKILL_FILE = "SKILL.md"
_REFERENCES_DIR = "references"
_SCRIPTS_DIR = "scripts"


class DirectorySkillLoader(SkillLoader):
    """Load skills from a local filesystem directory.

    Each subdirectory containing a SKILL.md file is treated as a skill.
    Optional ``references/`` and ``scripts/`` subdirectories provide
    resources and executable scripts respectively.

    Args:
        directory: Path to the root skills directory.
    """

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory).resolve()
        if not self._directory.is_dir():
            raise SkillLoaderError(
                f"Skills directory does not exist: {self._directory}"
            )

    def list_skills(self) -> list[SkillMetadata]:
        skills: list[SkillMetadata] = []
        for entry in sorted(self._directory.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / _SKILL_FILE
            if not skill_file.is_file():
                continue
            try:
                content = skill_file.read_text(encoding="utf-8")
                frontmatter, _ = parse_skill_md(content)
                metadata = frontmatter_to_metadata(frontmatter, source="local")
                skills.append(metadata)
            except (SkillValidationError, OSError):
                # Skip malformed skills during discovery
                continue
        return skills

    def load_skill(self, name: str) -> SkillContent:
        skill_dir = self._resolve_skill_dir(name)
        skill_file = skill_dir / _SKILL_FILE

        content = skill_file.read_text(encoding="utf-8")
        frontmatter, body = parse_skill_md(content)
        metadata = frontmatter_to_metadata(frontmatter, source="local")

        resources = self._list_dir_files(skill_dir / _REFERENCES_DIR)
        scripts = self._list_dir_files(skill_dir / _SCRIPTS_DIR)

        return SkillContent(
            metadata=metadata,
            body=body,
            resources=resources,
            scripts=scripts,
        )

    def read_resource(self, skill_name: str, resource_name: str) -> str:
        skill_dir = self._resolve_skill_dir(skill_name)
        resource_path = (skill_dir / _REFERENCES_DIR / resource_name).resolve()

        # Path traversal protection
        allowed_base = (skill_dir / _REFERENCES_DIR).resolve()
        if not resource_path.is_relative_to(allowed_base):
            raise SkillResourceNotFoundError(skill_name, resource_name)

        if not resource_path.is_file():
            raise SkillResourceNotFoundError(skill_name, resource_name)

        return resource_path.read_text(encoding="utf-8")

    def has_skill(self, name: str) -> bool:
        skill_dir = (self._directory / name).resolve()
        if not skill_dir.is_relative_to(self._directory):
            return False
        return skill_dir.is_dir() and (skill_dir / _SKILL_FILE).is_file()

    def read_script(self, skill_name: str, script_name: str) -> Path:
        skill_dir = self._resolve_skill_dir(skill_name)
        script_path = (skill_dir / _SCRIPTS_DIR / script_name).resolve()

        # Path traversal protection
        allowed_base = (skill_dir / _SCRIPTS_DIR).resolve()
        if not script_path.is_relative_to(allowed_base):
            raise SkillResourceNotFoundError(skill_name, script_name)

        if not script_path.is_file():
            raise SkillResourceNotFoundError(skill_name, script_name)

        return script_path

    def _resolve_skill_dir(self, name: str) -> Path:
        """Resolve and validate a skill directory by name."""
        skill_dir = (self._directory / name).resolve()
        if not skill_dir.is_relative_to(self._directory):
            raise SkillNotFoundError(name)
        if not skill_dir.is_dir() or not (skill_dir / _SKILL_FILE).is_file():
            raise SkillNotFoundError(name)
        return skill_dir

    @staticmethod
    def _list_dir_files(directory: Path) -> list[str]:
        """List filenames in a directory, or return empty if it doesn't exist."""
        if not directory.is_dir():
            return []
        return sorted(
            f.name for f in directory.iterdir() if f.is_file()
        )
