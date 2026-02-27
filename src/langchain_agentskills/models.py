"""Pydantic models for skill metadata and content."""

import re

from pydantic import BaseModel, field_validator

# Skill name: lowercase alphanumeric + hyphens, 1-64 chars,
# no leading/trailing/consecutive hyphens.
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")


def validate_skill_name(name: str) -> str:
    """Validate a skill name against the agentskills.io spec."""
    if "--" in name:
        raise ValueError(
            f"Invalid skill name '{name}': consecutive hyphens are not allowed"
        )
    if not SKILL_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid skill name '{name}': must be 1-64 lowercase alphanumeric "
            "characters and hyphens, no leading/trailing hyphens"
        )
    return name


class SkillMetadata(BaseModel):
    """Lightweight skill metadata for discovery (~100 tokens)."""

    name: str
    description: str
    license: str | None = None
    compatibility: dict | None = None
    metadata: dict | None = None
    allowed_tools: list[str] | None = None
    source: str = "local"

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        return validate_skill_name(v)


class SkillContent(BaseModel):
    """Full skill content: metadata + instructions + available files."""

    metadata: SkillMetadata
    body: str
    resources: list[str] = []
    scripts: list[str] = []
