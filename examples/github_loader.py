"""Live smoke test: GitHubSkillLoader + SkillMiddleware against the real repo."""

import shutil
import tempfile
from pathlib import Path

from langchain_agentskills import GitHubSkillLoader, SkillMiddleware


def main() -> None:
    print("=" * 60)
    print("Fetching skills from github.com/AnhQuanTrl/langchain-agentskills")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as td:
        cache = Path(td) / "cache"

        loader = GitHubSkillLoader(
            repo="AnhQuanTrl/langchain-agentskills",
            ref="main",
            subdir="test-skills/",
            cache_dir=cache,
            allow_scripts=True,
        )

        print(f"\ncache_dir: {cache}")
        print(f"extracted: {list(cache.iterdir())}")

        # 1. list_skills
        skills = loader.list_skills()
        print(f"\n--- list_skills() ---")
        for s in skills:
            print(f"  name={s.name!r}  source={s.source!r}")
            print(f"  description={s.description!r}")

        assert len(skills) == 1
        assert skills[0].name == "hello-world"
        assert skills[0].source == "github:AnhQuanTrl/langchain-agentskills@main"

        # 2. load_skill
        content = loader.load_skill("hello-world")
        print(f"\n--- load_skill('hello-world') ---")
        print(f"  resources: {content.resources}")
        print(f"  scripts:   {content.scripts}")
        print(f"  body (first 120 chars): {content.body[:120]!r}")

        assert "greeting.txt" in content.resources
        assert "greet.sh" in content.scripts  # visible because allow_scripts=True

        # 3. read_resource
        greeting = loader.read_resource("hello-world", "greeting.txt")
        print(f"\n--- read_resource('hello-world', 'greeting.txt') ---")
        print(f"  {greeting!r}")
        assert "{name}" in greeting

        # 4. read_script (allow_scripts=True)
        script_path = loader.read_script("hello-world", "greet.sh")
        print(f"\n--- read_script('hello-world', 'greet.sh') ---")
        print(f"  path: {script_path}")
        assert script_path.is_file()

        # 5. SkillMiddleware integration
        middleware = SkillMiddleware(loader=loader)
        print(f"\n--- SkillMiddleware(loader=<github>) ---")
        print(f"  tools registered: {[t.name for t in middleware.tools]}")

        # Show the injected system prompt
        injected = middleware._build_system_message(existing=None)
        print(f"\n--- Injected system prompt ---")
        # content is list of blocks
        for block in injected.content:
            if isinstance(block, dict):
                print(block.get("text", ""))
            else:
                print(block)

        # 6. Exercise a middleware tool directly
        load_tool = next(t for t in middleware.tools if t.name == "load_skill")
        result = load_tool.invoke({"skill_name": "hello-world"})
        print(f"\n--- load_skill tool invoke ---")
        # result is typically a structured string — print first 200 chars
        print(f"  {str(result)[:200]!r}...")

        read_tool = next(t for t in middleware.tools if t.name == "read_skill_resource")
        result2 = read_tool.invoke({"skill_name": "hello-world", "resource_name": "greeting.txt"})
        print(f"\n--- read_skill_resource tool invoke ---")
        print(f"  {str(result2)!r}")

        run_tool = next(t for t in middleware.tools if t.name == "run_skill_script")
        result3 = run_tool.invoke({
            "skill_name": "hello-world",
            "script_name": "greet.sh",
            "script_args": ["Arthur"],
        })
        print(f"\n--- run_skill_script tool invoke ---")
        print(f"  {str(result3)!r}")

        # 7. Test allow_scripts=False behaviour
        loader_safe = GitHubSkillLoader(
            repo="AnhQuanTrl/langchain-agentskills",
            ref="main",
            subdir="test-skills/",
            cache_dir=cache,  # reuse warm cache
            allow_scripts=False,
        )
        content_safe = loader_safe.load_skill("hello-world")
        print(f"\n--- load_skill with allow_scripts=False ---")
        print(f"  scripts: {content_safe.scripts}  (should be empty)")
        assert content_safe.scripts == []

        print("\n" + "=" * 60)
        print("ALL LIVE CHECKS PASSED")
        print("=" * 60)


if __name__ == "__main__":
    main()
