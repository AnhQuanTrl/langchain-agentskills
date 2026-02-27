"""SKILL.md parser: YAML frontmatter + markdown body."""

import yaml

from langchain_agentskills.exceptions import SkillValidationError
from langchain_agentskills.models import SkillMetadata

_FRONTMATTER_DELIMITER = "---"


def parse_skill_md(content: str) -> tuple[dict, str]:
    """Split a SKILL.md file into YAML frontmatter dict and markdown body.

    Args:
        content: Raw SKILL.md file content.

    Returns:
        Tuple of (frontmatter dict, markdown body string).

    Raises:
        SkillValidationError: If frontmatter is missing or malformed.
    """
    stripped = content.strip()
    if not stripped.startswith(_FRONTMATTER_DELIMITER):
        raise SkillValidationError(
            "SKILL.md must start with YAML frontmatter delimited by '---'"
        )

    # Find the closing delimiter
    rest = stripped[len(_FRONTMATTER_DELIMITER) :]
    end_idx = rest.find(f"\n{_FRONTMATTER_DELIMITER}")
    if end_idx == -1:
        raise SkillValidationError(
            "SKILL.md frontmatter is missing closing '---' delimiter"
        )

    yaml_str = rest[:end_idx]
    body = rest[end_idx + len(_FRONTMATTER_DELIMITER) + 1 :].strip()

    try:
        frontmatter = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise SkillValidationError(f"Invalid YAML in SKILL.md frontmatter: {e}") from e

    if not isinstance(frontmatter, dict):
        raise SkillValidationError("SKILL.md frontmatter must be a YAML mapping")

    return frontmatter, body


def frontmatter_to_metadata(frontmatter: dict, source: str = "local") -> SkillMetadata:
    """Validate frontmatter dict and convert to SkillMetadata.

    Args:
        frontmatter: Parsed YAML frontmatter dict.
        source: Origin identifier (e.g. "local", "github").

    Returns:
        Validated SkillMetadata instance.

    Raises:
        SkillValidationError: If required fields are missing or invalid.
    """
    try:
        return SkillMetadata(source=source, **frontmatter)
    except Exception as e:
        raise SkillValidationError(f"Invalid skill metadata: {e}") from e


def build_skill_md(metadata: SkillMetadata, body: str) -> str:
    """Reconstruct a SKILL.md file from metadata and body.

    Args:
        metadata: Skill metadata.
        body: Markdown instruction body.

    Returns:
        Complete SKILL.md file content.
    """
    # Only include non-None fields, exclude 'source' (not part of SKILL.md)
    data = metadata.model_dump(exclude={"source"}, exclude_none=True)
    yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{yaml_str}\n---\n\n{body}\n"
