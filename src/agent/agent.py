"""Main Living CLI Agent orchestrator"""
import requests
import json
import time
from typing import Tuple
from src.config import API_KEY, API_URL, MODEL_ID, Colors
from src.managers import ConversationManager, ToolManager
from src.parsers import StreamParser
from src.utils import format_tool_result, truncate_text


class Agent:
    """Main Living CLI Agent - orchestrates all components"""
    
    def __init__(self, api_key: str, api_url: str, model_id: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model_id = model_id
        self.log_path = "agent_chat.log"
        self.session_start = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Log session start
        self._log_event("session_start", {"model": model_id, "session_time": self.session_start})
        
        self.conversation = ConversationManager(
            system_prompt=(
                "You are a helpful assistant with access to tools that can extend dynamically. "
                "YOU CAN CREATE ANY TOOL YOU NEED - this is your superpower.\n"
                "\n"
                "Use the agentic reasoning approach:\n"
                "1. When given a task, identify which tools you need to accomplish it\n"
                "2. If you don't have a tool, CREATE IT using the 'create_tool' function\n"
                "3. Call the tool needed to gather information or complete the task\n"
                "4. After each tool executes, analyze the result carefully\n"
                "5. Decide the next action: call another tool to continue, or respond if complete\n"
                "6. Repeat until the task is fully completed\n"
                "\n"
                "CRITICAL - NEVER GIVE UP:\n"
                "- NEVER say 'I can't do this' or 'this is beyond my capabilities'\n"
                "- NEVER call end_chat just because a tool doesn't exist\n"
                "- If you need image generation, FILE operations, ANYTHING: CREATE A TOOL\n"
                "- The only reason to give up is if the user explicitly cancels\n"
                "- Always try: create_tool → use_tool → analyze_results → repeat\n"
                "\n"
                "CRITICAL - HONESTY AND LIMITATIONS:\n"
                "- NEVER guess or hallucinate information. Always use tools to verify facts.\n"
                "- If you don't know something, use a tool to check instead of guessing\n"
                "- NEVER claim a tool succeeded if you didn't actually call it\n"
                "- NEVER make up file contents, directory listings, or system information\n"
                "- If a tool returns no results, the answer is unknown - don't invent data\n"
                "- When checking directories, file existence, or system state: ALWAYS use appropriate tools\n"
                "\n"
                "TOOL USAGE HIERARCHY:\n"
                "1. Check what tools you ALREADY HAVE - use existing tools first\n"
                "2. If you need something you can't do, CREATE A TOOL for it (not instead of existing tools)\n"
                "3. Never create a tool when an existing tool can do the job\n"
                "4. Example: Don't create 'list_directory' if 'files' tool already exists\n"
                "\n"
                "CAPABILITY REFRAMING:\n"
                "- Instead of 'I can't do X': Think 'I can create a tool to do X'\n"
                "- Nothing is impossible - you can always create tools\n"
                "- But first, check if a tool already exists that can help\n"
                "\n"
                "YOUR CORE TOOLS (Use these FIRST before creating new tools):\n"
                "1. read_file (path) - Read file contents, check if file exists, list directories\n"
                "   Example: Check 'enhanced_mona_lisa.png' exists by reading the directory\n"
                "   STOP CREATING: check_file_exists, list_directory - use read_file instead!\n"
                "2. write_file (path, content) - Create or modify files\n"
                "3. open_browser (url) - Open URLs in browser or fetch web content\n"
                "4. get_current_time () - Get current date/time\n"
                "5. install_package (package, version) - Install Python dependencies\n"
                "6. create_tool (name, description, parameters, implementation) - Synthesize new tools\n"
                "7. update_tool (name, implementation) - Fix or improve existing tools\n"
                "8. remove_tool (name) - Delete auto-generated tools\n"
                "9. end_chat () - End the conversation (ONLY when task is complete or user exits)\n"
                "\n"
                "IMPORTANT: When you think 'I need to check if a file exists', just use read_file to check the directory.\n"
                "DO NOT create check_file_exists, list_files, or similar - these are covered by read_file!\n"
                "\n"
                "IMPORTANT: Between tool calls, think about what you learned and what you need to do next.\n"
                "\n"
                "CRITICAL REASONING RULES:\n"
                "- After EVERY tool execution, evaluate: Did this help? Do I have what I need?\n"
                "- If a tool gives you the answer, RESPOND to the user immediately - don't call it again!\n"
                "- Always summarize the results for the user in a clear, readable format\n"
                "- If a tool fails or gives incomplete data, try a DIFFERENT approach - not the same tool!\n"
                "- NEVER call the same tool twice in a row with the same arguments without changing strategy\n"
                "- If you're stuck after 2-3 attempts, explain the problem to the user and ask for guidance\n"
                "\n"
                "TOOL MANAGEMENT:\n"
                "- If you create duplicate or similar tools, use remove_tool to delete the old/broken ones\n"
                "- Keep your tool ecosystem clean by removing superseded tools\n"
                "- Example: if you create both 'get_ips' and 'get_ip_addresses', remove the weaker one\n"
                "\n"
                "CRITICAL - TOOL CALLING FORMAT:\n"
                "- This is an OpenAI-compatible API with standard function calling\n"
                "- When you want to use a tool, just express intent - the system handles the format\n"
                "- DO NOT manually write JSON or use tags like <tool_call>, <tool_sep>, etc.\n"
                "- The API will automatically handle tool formatting\n"
                "- DO: Clearly name the tool and its arguments; the API builds the function call\n"
                "- Example: read_file with file_path='D:/Documents/Reports/Attendance/file.xlsx'\n"
                "- Example: install_package with package='openpyxl'\n"
                "- Example: create_tool with name='my_tool', description='...', parameters={...}, implementation='...'\n"
                "- DO: Clearly name the tool and provide arguments; the API builds the call\n"
                "- DO NOT: Output raw JSON/XML or pseudo calls in text (e.g., read_file \"path\")\n"
                "- Example: If you need to read a file, just state: read_file with file_path='path' (no JSON/XML tags)\n"
                "\n"
                "TOOL SYNTHESIS: If a task would benefit from a custom tool that doesn't exist, use "
                "'create_tool' to synthesize a new tool. Provide name, description, JSON schema for parameters, "
                "and Python implementation. After creating a tool, you can immediately use it in subsequent steps.\n"
                "\n"
                "CRITICAL - JSON ESCAPING for create_tool:\n"
                "- The 'implementation' parameter is a Python code STRING that will be written to a file\n"
                "- Use SINGLE QUOTES for strings inside your Python code to avoid escaping issues\n"
                "- BAD: implementation='return \"hello world\", False' (requires escaping the double quotes)\n"
                "- GOOD: implementation='return \\'hello world\\', False' (single quotes, cleaner)\n"
                "- Avoid excessive backslashes - they cause syntax errors\n"
                "- Test your escaping: if you get SyntaxError, simplify your strings\n"
                "\n"
                "TOOL DEBUGGING: When a tool fails with an error:\n"
                "1. READ THE ERROR MESSAGE CAREFULLY - it tells you exactly what's wrong\n"
                "2. Analyze the root cause (missing module? wrong return format? logic error?)\n"
                "3. Use 'update_tool' ONCE to fix the specific issue\n"
                "4. ALWAYS TEST the tool after updating - don't update multiple times without testing!\n"
                "5. If it fails again, repeat from step 1\n"
                "\n"
                "CRITICAL: Never update a tool twice in a row without testing it in between!\n"
                "CRITICAL: Don't guess - fix the actual error shown in the message!\n"
                "\n"
                "DEPENDENCY MANAGEMENT:\n"
                "- If you get 'ModuleNotFoundError' or 'ImportError', use 'install_package' to install it\n"
                "- After installing, the package is immediately available - you can use it in tools\n"
                "- Prefer standard library when possible, but don't hesitate to install what you need\n"
                "- Example: Error 'No module named requests' → Call install_package(package='requests')\n"
                "\n"
                "INTERNET RESEARCH - Use web_search when you need information verification:\n"
                "- web_search is your general research tool for ANY uncertain information\n"
                "- Use it to verify facts, find solutions, get up-to-date information, research alternatives, and troubleshoot\n"
                "- Use 'web_search' whenever:\n"
                "  * You're unsure about how something works or if it's possible\n"
                "  * You need current/up-to-date information (library versions, best practices, etc.)\n"
                "  * You encounter errors or package issues and need solutions\n"
                "  * You need documentation or API reference information\n"
                "  * You want to research alternatives or best approaches\n"
                "- Example: 'How do I read Excel files in Python?' → web_search('read excel files python 2025')\n"
                "- Example: Unknown error about a package → web_search('error message python', search_type='error')\n"
                "- Example: Need specific package info → web_search('pandas documentation', search_type='docs')\n"
                "- Example: Want alternatives → web_search('Python Excel library alternatives')\n"
                "- NEVER assume information without checking - if uncertain, search for it\n"
                "\n"
                "CRITICAL for tool implementations: ALL code paths MUST return a 2-tuple: (message: str, should_exit: bool)\n"
                "Example: return 'Result: 42', False  (correct)\n"
                "BAD: return 'Result: 42'  (missing boolean - will crash)\n"
                "BAD: return value, True, extra  (too many values - will crash)\n"
                "\n"
                "Examples of multi-tool reasoning:\n"
                "- Task: 'Add the current time as a comment to main.py'\n"
                "  Step 1: Call get_current_time() → learn the time\n"
                "  Step 2: Call read_file(main.py) → understand file structure\n"
                "  Step 3: Call write_file() → add time comment based on what you learned\n"
                "\n"
                "- Task: 'Create a tool to reverse text, then use it on \"hello\"'\n"
                "  Step 1: Call create_tool() with implementation that reverses a string\n"
                "  Step 2: Call reverse_text(text='hello') → use your new tool\n"
                "\n"
                "Available tools: open_browser, get_current_time, read_file, write_file, create_tool, end_chat"
            )
        )
        self.tool_manager = ToolManager()
        self.stream_parser = StreamParser()
        
        # Add tools list to context for duplicate prevention
        self.available_tools = self.tool_manager.get_tool_definitions()

    def _log_event(self, kind: str, payload: dict):
        """Append structured logs to agent_chat.log for troubleshooting."""
        try:
            record = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, **payload}
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Logging should never break the agent
            pass
    
    def _log_message(self, role: str, content: str, context: str = ""):
        """Log full message content with role and optional context."""
        self._log_event("message", {
            "role": role,
            "context": context,
            "content": content[:2000] if len(content) > 2000 else content  # Limit very long content
        })
    
    def run(self):
        """Main chat loop"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}  Living CLI Agent - Connected to {self.model_id}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        # Display available tools in organized categories
        tool_names = [t["function"]["name"] for t in self.available_tools]
        
        print(f"{Colors.YELLOW}📦 Available Tools ({len(tool_names)} total):{Colors.RESET}")
        print(f"{Colors.CYAN}  Core:{Colors.RESET} read_file, write_file, open_browser, get_current_time, web_search")
        print(f"{Colors.CYAN}  Mgmt:{Colors.RESET} create_tool, update_tool, remove_tool, install_package")
        
        # Show custom tools if any exist
        custom_tools = [t for t in tool_names if t not in [
            "end_chat", "open_browser", "get_current_time", "read_file", "write_file",
            "web_search", "create_tool", "update_tool", "install_package", "remove_tool"
        ]]
        if custom_tools:
            custom_str = ", ".join(custom_tools[:5])  # Show first 5
            if len(custom_tools) > 5:
                custom_str += f" (+{len(custom_tools)-5} more)"
            print(f"{Colors.CYAN}  Custom:{Colors.RESET} {custom_str}")
        
        print(f"\n{Colors.GREEN}💡 Type your request or 'exit' to quit{Colors.RESET}")
        print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}\n")
        
        last_tool_used = None  # Track last tool to prevent consecutive update_tool calls
        last_tool_call = None  # Track last tool+args to detect infinite loops
        
        while True:
            try:
                # Get user input
                user_input = input(f"{Colors.GREEN}You: {Colors.RESET}").strip()
                
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if not user_input:
                    continue
                
                # Add to conversation
                self.conversation.add_user_message(user_input)
                self._log_message("user", user_input, "user_input")
                
                # Make API request
                should_exit = self._handle_turn()
                
                if should_exit:
                    break
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\n{Colors.RED}[Error] {e}{Colors.RESET}")
    
    def _handle_turn(self) -> bool:
        """
        Handle one conversation turn with agentic reasoning loop.
        The agent reasons about each tool result and decides the next action.
        Features: Step tracking, intermediate reasoning, error recovery, result formatting
        Returns True if should exit
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Agentic loop - continue until agent decides to respond or exit
        max_steps = 10
        step = 0
        tool_execution_count = 0  # Track total tools executed
        last_tool_signature = None  # Track (tool_name, args) to detect loops
        repeat_count = 0  # Count consecutive identical calls
        consecutive_errors = 0  # Track consecutive failed tool calls
        
        while step < max_steps:
            step += 1
            
            payload = {
                "model": self.model_id,
                "messages": self.conversation.get_messages(),
                "tools": self.tool_manager.get_tool_definitions(),
                "max_tokens": 2048,
                "temperature": 0.7,
                "stream": True
            }
            
            # Only print "Assistant:" on first step
            if step == 1:
                print(f"\n{Colors.CYAN}🤖 Assistant:{Colors.RESET} ", end="", flush=True)
            elif step > 1:
                # On reasoning steps, show what the agent is thinking
                print(f"\n{Colors.CYAN}🧠 Reasoning (Step {step}):{Colors.RESET} ", end="", flush=True)
            
            # Reset stream parser
            self.stream_parser.reset()
            
            # Stream the response
            stream_received_data = False
            stream_content = ""
            try:
                self._log_event("step_start", {
                    "step": step,
                    "max_steps": max_steps
                })
                
                with requests.post(self.api_url, headers=headers, json=payload, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        delta = self.stream_parser.process_line(line)
                        
                        if delta is None:
                            continue
                        
                        stream_received_data = True
                        
                        if delta.get('done'):
                            break
                        
                        # Print text on all steps
                        text = self.stream_parser.handle_delta(delta)
                        if text:
                            stream_content += text
                            print(text, end="", flush=True)
                
                # Check if stream was completely empty
                if not stream_received_data:
                    print(f"{Colors.YELLOW}[Warning]: Stream had no data. Retrying...{Colors.RESET}\n")
                    self._log_event("stream_empty", {"step": step})
                    if step < max_steps:
                        continue
                    else:
                        print(f"{Colors.RED}[Error]: No response data received from API{Colors.RESET}")
                        return False
            
            except requests.exceptions.RequestException as e:
                print(f"\n{Colors.RED}[Error] API request failed: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}[Recovery] Retrying...\n{Colors.RESET}")
                if step < max_steps:
                    continue
                else:
                    return False
            
            if step == 1:
                print()  # Newline after first response
            result = self.stream_parser.get_result()
            
            # Check for empty response - could indicate stream parsing issue
            if not result or (result["type"] == "text" and not result.get("content", "").strip()):
                print(f"{Colors.YELLOW}[Warning]: Received empty response from API. Retrying...{Colors.RESET}\n")
                self._log_event("empty_response", {
                    "step": step,
                    "result": result
                })
                if step < max_steps:
                    # Reset and try again
                    self.stream_parser.reset()
                    continue
                else:
                    print(f"{Colors.RED}[Error]: Max retries reached with empty responses{Colors.RESET}")
                    self._log_event("max_retries_empty", {"step": step})
                    return False
            
            # Log the parsing result
            if result["type"] == "tool_calls":
                self._log_event("parsed_tool_calls", {
                    "step": step,
                    "tool_count": len(result.get("tool_calls", [])),
                    "tools": [tc.get("function_name") for tc in result.get("tool_calls", [])]
                })
            else:
                self._log_message("assistant", result.get("content", ""), f"step_{step}_reasoning")
                self._log_event("parsed_text_response", {
                    "step": step,
                    "response_length": len(result.get("content", ""))
                })
            
            if result["type"] == "tool_calls":
                # Agent decided to use a tool
                tool_calls = result["tool_calls"]
                if not tool_calls:
                    print(f"{Colors.RED}[Error]: Failed to parse tool calls{Colors.RESET}")
                    print(f"{Colors.YELLOW}[Recovery]: Asking the agent to re-issue the tool call with valid JSON arguments and shorter payload if large.{Colors.RESET}\n")
                    recovery_msg = "Your previous tool call arguments were malformed or too long. Re-issue the tool call now with valid JSON arguments only (no extra text), keep payload concise, and let the API format it. If you need to send code, keep it minimal and valid JSON."
                    self.conversation.add_user_message(recovery_msg)
                    self._log_message("user", recovery_msg, "tool_parse_error_recovery")
                    continue
                    continue
                
                # Add agent's tool use to conversation (empty content for tool-only messages)
                self.conversation.add_assistant_message("")
                
                # Execute the tools with step tracking
                print(f"\n{Colors.YELLOW}{'─'*70}{Colors.RESET}")
                print(f"{Colors.YELLOW}⚡ Executing {len(tool_calls)} Tool(s) - Step {step}/{max_steps}{Colors.RESET}")
                print(f"{Colors.YELLOW}{'─'*70}{Colors.RESET}\n")
                
                should_exit = False
                for i, tool_call in enumerate(tool_calls, 1):
                    tool_execution_count += 1
                    func_name = tool_call["function_name"]
                    args = tool_call["arguments"]
                    
                    # Detect premature end_chat without even trying to solve the problem
                    if func_name == "end_chat" and step == 1:
                        reason = str(args.get("reason", "")).lower()
                        # Check if agent is giving up on solvable problems
                        give_up_patterns = ["capability", "can't", "cannot", "unable", "beyond", "don't have", "not available"]
                        if any(pattern in reason for pattern in give_up_patterns):
                            print(f"{Colors.RED}[INTERVENTION]: Agent tried to give up without attempting to solve!{Colors.RESET}")
                            print(f"{Colors.YELLOW}[Recovery]: You have create_tool - use it to solve the problem!{Colors.RESET}\n")
                            
                            # Inject strong message
                            self.conversation.add_assistant_message("")
                            self.conversation.add_user_message(
                                f"STOP: You were about to give up with reason '{reason}', but you CAN solve this! "
                                f"You have the 'create_tool' function which lets you build ANY tool you need. "
                                f"If you don't have image generation, create it. "
                                f"If you don't have something, build it. "
                                f"DO NOT call end_chat - try to accomplish the task instead."
                            )
                            continue
                    
                    # Create signature for this tool call
                    tool_signature = (func_name, json.dumps(args, sort_keys=True))
                    
                    # Check for identical repeated calls
                    if tool_signature == last_tool_signature:
                        repeat_count += 1
                        if repeat_count >= 2:
                            print(f"{Colors.RED}[Warning]: Agent is repeating the same tool call!{Colors.RESET}")
                            print(f"{Colors.YELLOW}[Intervention]: Breaking loop and forcing response{Colors.RESET}\n")
                            # Add intervention message
                            self.conversation.add_tool_result(
                                tool_call_id=tool_call["id"],
                                function_name=func_name,
                                result=(
                                    f"SYSTEM INTERVENTION: You've called {func_name} with identical arguments 3 times. "
                                    f"This is not productive. You must either:\n"
                                    f"1. RESPOND to the user with what you've learned, OR\n"
                                    f"2. Try a DIFFERENT tool or approach, OR\n"
                                    f"3. Explain what's blocking you\n"
                                    f"DO NOT call the same tool again!"
                                )
                            )
                            # Reset and continue to force agent to respond
                            last_tool_signature = None
                            repeat_count = 0
                            continue
                    else:
                        last_tool_signature = tool_signature
                        repeat_count = 0
                    
                    # Check for consecutive update_tool calls
                    if func_name == "update_tool" and last_tool_used == "update_tool":
                        print(f"{Colors.RED}[Warning]: Consecutive update_tool detected! You must TEST the tool before updating again.{Colors.RESET}\n")
                        # Add warning to conversation for agent to see
                        self.conversation.add_tool_result(
                            tool_call_id=tool_call["id"],
                            function_name=func_name,
                            result="ERROR: You updated a tool without testing it first! You must call the updated tool to verify it works before updating it again. Test-first approach required."
                        )
                        last_tool_used = func_name
                        continue
                    
                    # Check if agent is trying to create a tool that already exists
                    if func_name == "create_tool":
                        tool_name = args.get("name", "").strip()
                        existing_tools = [t["function"]["name"] for t in self.available_tools]
                        
                        if tool_name in existing_tools:
                            print(f"{Colors.RED}[Warning]: Tool '{tool_name}' already exists!{Colors.RESET}\n")
                            self.conversation.add_tool_result(
                                tool_call_id=tool_call["id"],
                                function_name=func_name,
                                result=f"ERROR: Tool '{tool_name}' already exists! You should update it with 'update_tool' instead, or use a different name. Existing tools: {', '.join(existing_tools)}"
                            )
                            last_tool_used = func_name
                            continue
                    
                    print(f"{Colors.YELLOW}🔧 Tool {i}/{len(tool_calls)}: {Colors.RESET}{Colors.CYAN}{func_name}{Colors.RESET}")
                    if args:
                        print(f"   {Colors.CYAN}├─ Args:{Colors.RESET} {args}")
                    else:
                        print(f"   {Colors.CYAN}├─ Args:{Colors.RESET} (none)")
                    
                    self._log_message("tool_call", json.dumps({"function": func_name, "arguments": args}), f"step_{step}")
                    
                    try:
                        tool_result, exit_flag = self.tool_manager.execute_tool(func_name, args)
                        
                        # Format and display the result (truncate if needed)
                        formatted_result = format_tool_result(tool_result, func_name)
                        result_display = truncate_text(tool_result, max_length=300)
                        print(f"   {Colors.CYAN}└─ Result:{Colors.RESET} {result_display}")
                        print()  # Blank line for spacing

                        # Log tool result
                        self._log_message("tool_result", tool_result, f"tool_{func_name}_step_{step}")
                        
                        # Track success/failure
                        if "Error" in tool_result or "error" in tool_result.lower():
                            consecutive_errors += 1
                        else:
                            consecutive_errors = 0  # Reset on success
                        
                        # Add full result to conversation
                        self.conversation.add_tool_result(
                            tool_call_id=tool_call["id"],
                            function_name=func_name,
                            result=tool_result
                        )
                        
                        # Track last tool used
                        last_tool_used = func_name
                        
                        if exit_flag:
                            should_exit = True
                    
                    except Exception as e:
                        error_msg = f"Error executing {func_name}: {str(e)}"
                        print(f"   {Colors.RED}└─ Error:{Colors.RESET} {error_msg}")
                        print()
                        self.conversation.add_tool_result(
                            tool_call_id=tool_call["id"],
                            function_name=func_name,
                            result=error_msg
                        )
                        consecutive_errors += 1
                
                # Check if agent is stuck with repeated errors
                if consecutive_errors >= 3:
                    print(f"\n{Colors.RED}{'='*70}{Colors.RESET}")
                    print(f"{Colors.RED}⚠️  WARNING: Agent appears stuck with repeated errors{Colors.RESET}")
                    print(f"{Colors.RED}{'='*70}{Colors.RESET}")
                    print(f"{Colors.YELLOW}The agent has failed {consecutive_errors} consecutive tool calls.{Colors.RESET}")
                    print(f"{Colors.YELLOW}This suggests the current approach isn't working.{Colors.RESET}\n")
                    print(f"{Colors.CYAN}💡 Agent needs to try a different strategy or explain the problem.{Colors.RESET}\n")
                    
                    self._log_event("consecutive_errors_intervention", {
                        "step": step,
                        "consecutive_errors": consecutive_errors,
                        "recent_failed_tools": [tc["function_name"] for tc in tool_calls[-3:]]
                    })

                    # Add intervention to force reflection
                    intervention_msg = (
                        f"CRITICAL: {consecutive_errors} consecutive failures. You are stuck in a loop.\\n\\n"
                        "MANDATORY ACTIONS:\\n"
                        "1. READ THE ERROR: What is the actual technical error message?\\n"
                        "2. IDENTIFY ROOT CAUSE: Why is it failing? (dependency missing? syntax error? wrong approach?)\\n"
                        "3. CHANGE YOUR APPROACH COMPLETELY: Do not retry the same failing action.\\n\\n"
                        "SPECIFIC GUIDANCE:\\n"
                        "- Tool creation syntax errors? Check JSON escaping - use single quotes in strings, avoid excessive backslashes\\n"
                        "- Package installation fails? Try simpler pure-Python alternatives or use web_search for solutions\\n"
                        "- Fundamental approach broken? Try a completely different method\\n\\n"
                        "EXECUTE A DIFFERENT STRATEGY NOW. Do not repeat what just failed."
                    )
                    self.conversation.add_user_message(intervention_msg)
                    consecutive_errors = 0  # Reset after intervention
                
                # If any tool requested exit, stop the loop
                if should_exit:
                    return True
                
                # Show what's next
                if step == 1:
                    print(f"{Colors.YELLOW}{'─'*70}{Colors.RESET}")
                    print(f"{Colors.CYAN}📊 Analyzing results...{Colors.RESET}")
                    print(f"{Colors.YELLOW}{'─'*70}{Colors.RESET}\n")
                
                # After first tool execution, if we got good results, push agent to respond
                # by injecting a message asking to summarize findings
                if step == 2 and tool_execution_count > 0:
                    # Check if recent tool results look complete (not error-like)
                    messages = self.conversation.get_messages()
                    last_tool_result = None
                    for msg in reversed(messages):
                        if msg.get("role") == "tool":
                            last_tool_result = msg.get("content", "")
                            break
                    
                    # If we have a result that's not an error, nudge agent to respond
                    if last_tool_result and "error" not in last_tool_result.lower():
                        self.conversation.add_user_message(
                            "Based on the tool results above, please provide a clear summary of what you found to answer my original request."
                        )
                
                # Loop continues - agent will reason about tool results and decide next action
                continue
            
            else:
                # Agent decided to respond with text
                response_text = result.get("content", "").strip()
                
                # If response is still empty after all checks, retry
                if not response_text:
                    print(f"{Colors.YELLOW}[Warning]: Response text is empty. Retrying...{Colors.RESET}\n")
                    if step < max_steps:
                        continue
                    else:
                        print(f"{Colors.RED}[Error]: No valid response received after {max_steps} attempts{Colors.RESET}")
                        return False
                
                # Detect if the agent is outputting malformed tool syntax
                malformed_patterns = [
                    "<tool_call>", "<function_call>", "<tool_sep>", "</tool_call>", "</function_call>",
                    "<invoke>", "</invoke>"
                ]
                has_malformed = any(pattern in response_text for pattern in malformed_patterns)
                
                # Also check for raw JSON function calls at start
                if not has_malformed and response_text.startswith("{"):
                    if '"name":' in response_text or '"function"' in response_text or '"arguments"' in response_text:
                        has_malformed = True
                
                if has_malformed:
                    print(f"\n{Colors.RED}{'='*70}{Colors.RESET}")
                    print(f"{Colors.RED}❌ ERROR: Invalid Tool Calling Format Detected{Colors.RESET}")
                    print(f"{Colors.RED}{'='*70}{Colors.RESET}")
                    print(f"{Colors.YELLOW}The agent emitted XML/JSON tool syntax instead of using the API properly.{Colors.RESET}")
                    print(f"{Colors.YELLOW}Recovery: Forcing a retry with a clear instruction to call tools via function-calling (no raw JSON/XML).{Colors.RESET}\n")

                    self._log_message("malformed_syntax_detected", response_text[:500], f"step_{step}malformed")

                    # Inject guidance so the model fixes itself without asking the user
                    recovery = (
                        "CRITICAL ERROR: You used malformed tool syntax. Stop using XML/JSON tags.\n\n"
                        "WRONG: <tool_call>read_file<tool_sep>{...}</tool_call>\n"
                        "WRONG: {\"name\": \"read_file\", \"arguments\": {...}}\n"
                        "WRONG: 'read_file(...)' as plain text\n\n"
                        "RIGHT: Use the API's function calling mechanism. Just invoke the function.\n\n"
                        "RETRY NOW: Execute the tool using function calling (no text, no XML, no JSON)."
                    )
                    self.conversation.add_user_message(recovery)
                    continue

                # Detect plain-text pseudo tool calls like "read_file <path>" that should have been real calls
                tool_names = [t["function"]["name"] for t in self.tool_manager.get_tool_definitions()]
                lowered = response_text.lower()
                pseudo_call = False
                for name in tool_names:
                    if lowered.startswith(f"{name} ") or lowered.startswith(f"{name}(") or lowered.startswith(f"{name}{{") or f"{name}(" in lowered:
                        pseudo_call = True
                        break
                if pseudo_call:
                    print(f"{Colors.YELLOW}[Warning]: Assistant described a tool call in text instead of executing it.{Colors.RESET}\n")
                    self._log_message("pseudo_tool_call", response_text[:500], f"step_{step}")
                    recovery_msg = (
                        "ERROR: You described a tool call as text instead of executing it.\n\n"
                        "What you did: Wrote text like 'read_file with file_path=...'\n"
                        "What you MUST do: Use the API's function calling to execute the tool.\n\n"
                        "STOP writing text. START using actual function calls.\n"
                        "EXECUTE THE TOOL NOW (no text description, actual function call)."
                    )
                    self.conversation.add_user_message(recovery_msg)
                    self._log_message("user", recovery_msg, "pseudo_call_recovery")
                    continue
                
                self.conversation.add_assistant_message(response_text)
                self._log_message("assistant", response_text, f"step_{step}_final")
                
                # Check if the response indicates the agent wants to continue (more tools needed)
                continuation_indicators = [
                    "i will", "i'll", "let me", "i need to", "next", "now i", "first", "then",
                    "i should", "i can", "i'm going to", "step ", "after that"
                ]
                wants_to_continue = any(indicator in response_text.lower() for indicator in continuation_indicators)
                
                # If agent seems to want to continue and we haven't hit max steps, let it continue
                if wants_to_continue and step < max_steps:
                    print(f"\n{Colors.CYAN}{'─'*70}{Colors.RESET}")
                    print(f"{Colors.CYAN}💭 Agent reasoning... (Step {step}/{max_steps}){Colors.RESET}")
                    print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}\n")
                    continue  # Let the agent continue to next step
                
                # Otherwise, treat as completion
                if tool_execution_count > 0:
                    print(f"\n{Colors.GREEN}{'─'*70}{Colors.RESET}")
                    print(f"{Colors.GREEN}✅ Task Complete: {tool_execution_count} tool(s) executed across {step} step(s){Colors.RESET}")
                    print(f"{Colors.GREEN}{'─'*70}{Colors.RESET}\n")
                    
                    self._log_event("task_complete", {
                        "step": step,
                        "tool_count": tool_execution_count,
                        "response_length": len(response_text)
                    })
                return False
        
        # Max steps reached
        print(f"{Colors.YELLOW}[Warning]: Max agent steps reached ({max_steps}). Task may be incomplete.{Colors.RESET}")
        self._log_event("max_steps_reached", {
            "max_steps": max_steps,
            "tools_executed": tool_execution_count,
            "final_messages_count": len(self.conversation.get_messages())
        })
        return False
