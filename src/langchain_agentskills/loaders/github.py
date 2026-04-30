"""Load skills from a GitHub repository via the tarball API."""

from __future__ import annotations

import os
import re
import shutil
import tarfile
import tempfile
from collections.abc import Iterable
from pathlib import Path

import httpx

from langchain_agentskills.exceptions import SkillLoaderError
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.loaders.directory import DirectorySkillLoader
from langchain_agentskills.models import SkillContent, SkillMetadata

_REF_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]")


def _slug(ref: str) -> str:
    return _REF_SLUG_UNSAFE.sub("-", ref)


def _default_cache_root() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "langchain-agentskills" / "github"
    return Path.home() / ".cache" / "langchain-agentskills" / "github"


def _resolve_token(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


class GitHubSkillLoader(SkillLoader):
    """Load skills from a (possibly private) GitHub repository.

    Fetches a tarball at ``ref`` from the GitHub REST API once at construction,
    extracts it into a local cache directory, and delegates file operations
    to an internal ``DirectorySkillLoader``.

    Args:
        repo: Repository in ``"owner/name"`` form.
        ref: Branch, tag, or commit SHA. Defaults to ``"main"``.
        token: GitHub token. Falls back to ``GITHUB_TOKEN`` / ``GH_TOKEN``.
        subdir: Path inside the repo where skills live (e.g. ``"skills/"``).
        cache_dir: Override for the cache directory location.
        allow_scripts: When ``False`` (default), :meth:`read_script` raises
            and ``scripts`` are stripped from ``load_skill`` results so the
            agent does not attempt to execute them.
        include: If set, only skills whose names match at least one of these
            ``fnmatch`` patterns are loaded.
        exclude: Skills whose names match any of these ``fnmatch`` patterns
            are hidden. Applied after ``include``.
    """

    def __init__(
        self,
        repo: str,
        *,
        ref: str = "main",
        token: str | None = None,
        subdir: str = "",
        cache_dir: str | Path | None = None,
        allow_scripts: bool = False,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> None:
        if repo.count("/") != 1 or not all(repo.split("/")):
            raise ValueError(f"repo must be 'owner/name', got: {repo!r}")

        subdir = subdir.strip("/")
        if subdir and ".." in Path(subdir).parts:
            raise ValueError(f"subdir must not contain '..': {subdir!r}")

        self._repo = repo
        self._ref = ref
        self._token = _resolve_token(token)
        self._subdir = subdir
        self._allow_scripts = allow_scripts
        self._include = tuple(include) if include is not None else None
        self._exclude = tuple(exclude) if exclude is not None else None

        owner, name = repo.split("/", 1)
        if cache_dir is None:
            self._cache_dir = _default_cache_root() / f"{owner}-{name}-{_slug(ref)}"
        else:
            self._cache_dir = Path(cache_dir).resolve()

        if not self._cache_dir.exists() or not any(self._cache_dir.iterdir()):
            self._fetch_and_extract()

        self._inner = self._build_inner_loader()
        self._source_label = f"github:{self._repo}@{self._ref}"

    def refresh(self) -> None:
        """Wipe the cache and re-fetch the tarball."""
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
        self._fetch_and_extract()
        self._inner = self._build_inner_loader()

    def _build_inner_loader(self) -> DirectorySkillLoader:
        root = self._find_extracted_root()
        skills_root = root / self._subdir if self._subdir else root
        if not skills_root.is_dir():
            raise SkillLoaderError(
                f"subdir {self._subdir!r} not found in {self._repo}@{self._ref}"
            )
        return DirectorySkillLoader(
            skills_root,
            include=self._include,
            exclude=self._exclude,
        )

    def _fetch_and_extract(self) -> None:
        url = f"https://api.github.com/repos/{self._repo}/tarball/{self._ref}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise SkillLoaderError(
                f"failed to create cache dir {self._cache_dir}; "
                f"filesystem may be read-only: {e}"
            ) from e

        try:
            with httpx.Client(follow_redirects=True, timeout=60) as client:
                with client.stream("GET", url, headers=headers) as response:
                    self._check_response(response)
                    with tempfile.SpooledTemporaryFile(
                        max_size=16 * 1024 * 1024
                    ) as buf:
                        for chunk in response.iter_bytes():
                            buf.write(chunk)
                        buf.seek(0)
                        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                            tar.extractall(self._cache_dir, filter="data")
        except httpx.HTTPError as e:
            raise SkillLoaderError(
                f"failed to fetch {self._repo}@{self._ref} from GitHub: {e}"
            ) from e

    @staticmethod
    def _check_response(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise SkillLoaderError(
                "GitHub auth failed (check GITHUB_TOKEN / GH_TOKEN or the "
                "passed token)"
            )
        if (
            response.status_code == 403
            and response.headers.get("X-RateLimit-Remaining") == "0"
        ):
            raise SkillLoaderError(
                "GitHub rate limit hit; a token increases the limit to 5000/hr"
            )
        if response.status_code == 404:
            raise SkillLoaderError(
                "repo or ref not found, or token lacks access "
                "(GitHub returns 404 for both)"
            )
        response.raise_for_status()

    def _find_extracted_root(self) -> Path:
        entries = [e for e in self._cache_dir.iterdir() if e.is_dir()]
        if len(entries) != 1:
            raise SkillLoaderError(
                f"unexpected tarball layout in {self._cache_dir}: "
                f"expected 1 top-level dir, got {len(entries)}"
            )
        return entries[0]

    def list_skills(self) -> list[SkillMetadata]:
        skills = self._inner.list_skills()
        for s in skills:
            s.source = self._source_label
        return skills

    def load_skill(self, name: str) -> SkillContent:
        content = self._inner.load_skill(name)
        content.metadata.source = self._source_label
        if not self._allow_scripts:
            content.scripts = []
        return content

    def read_resource(self, skill_name: str, resource_name: str) -> str:
        return self._inner.read_resource(skill_name, resource_name)

    def has_skill(self, name: str) -> bool:
        return self._inner.has_skill(name)

    def read_script(self, skill_name: str, script_name: str) -> Path:
        if not self._allow_scripts:
            raise SkillLoaderError(
                f"remote scripts disabled for {self._source_label}; "
                "set allow_scripts=True to opt in"
            )
        return self._inner.read_script(skill_name, script_name)
