# langchain-agentskills

[agentskills.io](https://agentskills.io) support for LangChain and LangGraph.

## Install

```bash
pip install langchain-agentskills
```

## Quick Start

### Toolkit (classic)

```python
from langchain.agents import create_agent
from langchain_agentskills import SkillsToolkit

toolkit = SkillsToolkit(directories=["./skills"])

agent = create_agent(
    model="gpt-5.2",
    tools=toolkit.get_tools(),
    system_prompt=toolkit.get_instructions(),
)
```

### Middleware (recommended)

```python
from langchain.agents import create_agent
from langchain_agentskills import DirectorySkillLoader, SkillMiddleware

loader = DirectorySkillLoader("./skills")

agent = create_agent(
    model="gpt-5.2",
    middleware=[SkillMiddleware(loader=loader)],
)
```

The middleware automatically injects skill descriptions into the system prompt and registers `load_skill`, `read_skill_resource`, and `run_skill_script` tools.

## Skill directory structure

```
skills/
  my-skill/
    SKILL.md          # Frontmatter + instructions
    references/       # Resource files the agent can read
      api-spec.yaml
    scripts/          # Executable scripts the agent can run
      deploy.sh
```

`SKILL.md` uses YAML frontmatter:

```markdown
---
name: my-skill
description: Short description for the agent
version: "1.0"
tags: [deployment, ci]
---

# Instructions

Detailed instructions for the agent...
```

## Custom loaders

Implement `SkillLoader` to load skills from any source (Git, S3, database, etc.):

```python
from langchain_agentskills import SkillLoader

class MyGitLoader(SkillLoader):
    def list_skills(self): ...
    def load_skill(self, name): ...
    def read_resource(self, skill_name, resource_name): ...
    def read_script(self, skill_name, script_name): ...
    def has_skill(self, name): ...
```

Use with the toolkit or middleware:

```python
# Toolkit
toolkit = SkillsToolkit(loaders=[MyGitLoader(...)])

# Middleware
middleware = SkillMiddleware(loader=MyGitLoader(...))
```

## License

MIT
