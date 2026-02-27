"""Hello World example: using langchain-agentskills with a LangChain agent.

Usage:
    export OPENAI_API_KEY="sk-..."
    uv run --extra examples python examples/hello_world.py
"""

from pathlib import Path

from langchain.agents import create_agent

from langchain_agentskills import SkillsToolkit

SKILLS_DIR = Path(__file__).parent / "skills"

# 1. Create the toolkit pointing at local skills
toolkit = SkillsToolkit(directories=[str(SKILLS_DIR)])

# 2. Build an agent with GPT-5.2 + skill tools
#    get_instructions() injects skill names into the system prompt so the
#    agent already knows what's available without calling list_skills first.
agent = create_agent(
    model="gpt-5.2",
    tools=toolkit.get_tools(),
    system_prompt=toolkit.get_instructions(),
)

# 3. Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Greet Alice in a formal style using available skills."}]}
)

for msg in result["messages"]:
    role = getattr(msg, "type", "unknown")

    # AI messages with tool calls show up with empty content
    if role == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"[tool_call] {tc['name']}({tc['args']})")
    elif role == "tool":
        print(f"[tool_result] {msg.content[:200]}")
    else:
        print(f"[{role}] {msg.content}")
