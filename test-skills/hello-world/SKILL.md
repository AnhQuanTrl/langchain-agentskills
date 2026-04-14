---
name: hello-world
description: Greets a user by name using a configurable greeting template
---

# Hello World

Use this skill when the user asks to be greeted, welcomed, or says hello.

## Steps

1. Read the greeting template from `references/greeting.txt`.
2. Substitute the user's name into the template (replace `{name}`).
3. Return the personalized greeting.

## Example

User: "Say hi to Arthur."
Assistant: `Hello, Arthur! Welcome to langchain-agentskills.`
