#!/usr/bin/env python3
"""Check for context overflow and system prompt size"""
import json
from src.agent.agent import Agent
from src.config import API_KEY, API_URL, MODEL_ID

print("=" * 100)
print("SYSTEM PROMPT SIZE ANALYSIS:")
print("=" * 100)

# Create a temporary agent to check system prompt
agent = Agent(api_key=API_KEY, api_url=API_URL, model_id=MODEL_ID)
messages = agent.conversation.get_messages()
system_msg = messages[0]

system_content = system_msg.get('content', '')
print(f"\nSystem prompt length: {len(system_content):,} characters")
print(f"System prompt tokens (~4 chars/token): ~{len(system_content) // 4:,} tokens")
print(f"\nSystem prompt preview (first 200 chars):")
print(f"  {system_content[:200]}...\n")

# Now analyze the log file
print("=" * 100)
print("LOG FILE ANALYSIS:")
print("=" * 100)

with open('agent_chat.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"\nTotal log entries: {len(lines)}\n")

# Analyze context
message_count = 0
assistant_messages = 0
total_chars = 0

for line in lines:
    try:
        record = json.loads(line)
        if record.get('kind') == 'message':
            message_count += 1
            role = record.get('role', '')
            content = record.get('content', '')
            total_chars += len(content)
            if role == 'assistant':
                assistant_messages += 1
    except:
        pass

print(f"Message entries in log: {message_count}")
print(f"Assistant messages: {assistant_messages}")
print(f"Total message characters: {total_chars:,}")
print(f"Estimated tokens (4 chars = 1 token): {total_chars // 4:,}")
print(f"\nTotal context estimate (system + messages): ~{(len(system_content) + total_chars) // 4:,} tokens")

# DeepSeek-v3 has 128K context window
context_limit = 128000
estimated_tokens = (len(system_content) + total_chars) // 4
print(f"Context window limit: {context_limit:,} tokens")
print(f"Usage: {(estimated_tokens / context_limit) * 100:.1f}%")

if estimated_tokens > context_limit * 0.7:
    print(f"⚠️  WARNING: Context usage is {(estimated_tokens / context_limit) * 100:.1f}% - approaching limit!")
elif estimated_tokens > context_limit * 0.5:
    print(f"⚠️  CAUTION: Context usage is {(estimated_tokens / context_limit) * 100:.1f}% - monitor closely")
else:
    print(f"✅ Context usage is healthy at {(estimated_tokens / context_limit) * 100:.1f}%")

# Find hallucination patterns
print("\n" + "=" * 100)
print("HALLUCINATION DETECTION:")
print("=" * 100)

hallucination_found = False
for i, line in enumerate(lines[-50:], start=len(lines)-50):  # Check last 50 entries
    try:
        record = json.loads(line)
        if record.get('kind') == 'message' and record.get('role') == 'assistant':
            content = record.get('content', '')
            context = record.get('context', '')
            
            # Check for off-topic content
            hallucination_markers = ['binary tree', 'leetcode', 'data structures', 'ai and ml', 'algorithm', 'evolution of', 'machine learning']
            if any(marker in content.lower() for marker in hallucination_markers):
                hallucination_found = True
                print(f"\n🚨 HALLUCINATION DETECTED at entry {i}")
                print(f"   Context: {context}")
                print(f"   Content preview: {content[:200]}")
    except:
        pass

if not hallucination_found:
    print("\n✅ No hallucinations detected in recent logs")

# Analyze system prompt sections
print("\n" + "=" * 100)
print("SYSTEM PROMPT BREAKDOWN:")
print("=" * 100)

sections = system_content.split('\n\n')
print(f"\nTotal sections: {len(sections)}")
for i, section in enumerate(sections[:10], 1):
    lines_in_section = section.count('\n')
    chars = len(section)
    print(f"  Section {i}: {chars:,} chars, {lines_in_section} lines - {section[:60]}...")
