#!/usr/bin/env python3
"""Replace verbose system prompt with simplified version"""
import re

# Read the file
with open('src/agent/agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The simplified system prompt - MUCH shorter and clearer
new_prompt = r'''system_prompt=(
                "You are a helpful AI assistant with access to tools.\n"
                "\n"
                "TOOLS YOU HAVE:\n"
                "- read_file: Read files, check if they exist, list directories\n"
                "- write_file: Create or modify files\n"
                "- install_package: Install Python packages\n"
                "- create_tool: Build new custom tools\n"
                "- update_tool: Fix or improve existing tools\n"
                "- web_search: Research information online\n"
                "- get_current_time: Get the current date/time\n"
                "- open_browser: Open URLs\n"
                "- end_chat: End the conversation\n"
                "\n"
                "YOUR WORKFLOW:\n"
                "1. Understand the user's request\n"
                "2. Choose which tools to use\n"
                "3. Call the tools in the right order\n"
                "4. Analyze the results\n"
                "5. Respond with clear information\n"
                "\n"
                "RULES:\n"
                "- Always use tools to verify facts - never guess\n"
                "- After each tool, decide if you need more tools or can respond\n"
                "- If a tool gives the answer, respond immediately\n"
                "- Do NOT write fake tool calls or JSON/XML - just use the tools\n"
                "- Never make up file contents or system information\n"
                "- If unsure about facts, use web_search\n"
                "- Always respond with summaries of what you found\n"
            )'''

# Find and replace - use a more flexible pattern
pattern = r'system_prompt=\(\s*"[^"]*You are a helpful assistant.*?\n\s*\)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print(f"Found system_prompt at position {match.start()}-{match.end()}")
    print(f"Old length: {match.end() - match.start()} chars")
    
    # Replace
    new_content = content[:match.start()] + new_prompt + content[match.end():]
    
    # Write back
    with open('src/agent/agent.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ System prompt simplified!")
    print(f"New prompt length: {len(new_prompt)} chars")
    print(f"Reduction: ~{(match.end() - match.start() - len(new_prompt)) / (match.end() - match.start()) * 100:.1f}%")
else:
    print("❌ Could not find system_prompt pattern")
    # Try alternative pattern
    if 'system_prompt=' in content:
        print("Found 'system_prompt=' in file but pattern didn't match")
