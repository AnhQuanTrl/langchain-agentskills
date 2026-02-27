"""Hello World example: using SkillMiddleware with a LangChain agent.

This example uses the middleware API instead of the toolkit pattern.
The middleware automatically injects skill descriptions into the system
prompt and registers skill tools with the agent.

Usage:
    export OPENAI_API_KEY="sk-..."
    uv run --extra examples python examples/hello_world_middleware.py
"""

from pathlib import Path

from langchain.agents import create_agent

from langchain_agentskills import DirectorySkillLoader, SkillMiddleware

SKILLS_DIR = Path(__file__).parent / "skills"

# 1. Create a loader and middleware
loader = DirectorySkillLoader(SKILLS_DIR)
skill_middleware = SkillMiddleware(loader=loader)

# 2. Build an agent with the middleware — it handles tool registration
#    and system prompt injection automatically.
agent = create_agent(
    model="gpt-5.2",
    middleware=[skill_middleware],
)

# 3. Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Greet Alice in a formal style using available skills."}]}
)

for msg in result["messages"]:
    role = getattr(msg, "type", "unknown")

    if role == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"[tool_call] {tc['name']}({tc['args']})")
    elif role == "tool":
        print(f"[tool_result] {msg.content[:200]}")
    else:
        print(f"[{role}] {msg.content}")
