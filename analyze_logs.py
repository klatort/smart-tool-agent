#!/usr/bin/env python3
"""Analyze agent_chat.log to find errors and hallucinations"""
import json

with open('agent_chat.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total log entries: {len(lines)}\n")

# Print last 60 lines which should show the hallucination/error
print("=" * 100)
print("LAST 60 LOG ENTRIES (most recent):")
print("=" * 100)
for i, line in enumerate(lines[-60:], start=len(lines)-60):
    try:
        record = json.loads(line)
        ts = record.get('ts', '')
        kind = record.get('kind', '')
        
        if kind == 'message':
            role = record.get('role', '')
            context = record.get('context', '')
            content = record.get('content', '')
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"\n[Line {i}] [{ts}] MESSAGE")
            print(f"  Role: {role}")
            print(f"  Context: {context}")
            print(f"  Content: {content}")
        else:
            # Show non-message events more compactly
            print(f"[Line {i}] [{ts}] {kind:20} | {json.dumps(record, ensure_ascii=False)[:120]}")
    except Exception as e:
        print(f"[Line {i}] [ERROR PARSING] {str(e)[:100]}")
        print(f"  Raw: {line[:150]}")
