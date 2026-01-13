"""Main Living CLI Agent orchestrator"""
import requests
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
        
        self.conversation = ConversationManager(
            system_prompt=(
                "You are a helpful assistant with access to tools that can extend dynamically. "
                "Use the agentic reasoning approach:\n"
                "1. When given a task, identify which tools you need to accomplish it\n"
                "2. Call the first tool needed to gather information\n"
                "3. After each tool executes, analyze the result carefully\n"
                "4. Decide the next action: call another tool to continue, or respond if complete\n"
                "5. Repeat until the task is fully completed\n"
                "\n"
                "IMPORTANT: Between tool calls, think about what you learned and what you need to do next.\n"
                "\n"
                "TOOL SYNTHESIS: If a task would benefit from a custom tool that doesn't exist, use "
                "'create_tool' to synthesize a new tool. Provide name, description, JSON schema for parameters, "
                "and Python implementation. After creating a tool, you can immediately use it in subsequent steps.\n"
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
                "CRITICAL: Standard library only - no 'requests', no 'pandas', etc. Use urllib.request instead!\n"
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
    
    def run(self):
        """Main chat loop"""
        print(f"{Colors.CYAN}--- Connected to {self.model_id} ---{Colors.RESET}")
        print(f"{Colors.YELLOW}Available tools: browser, time, files, end_chat{Colors.RESET}\n")
        
        last_tool_used = None  # Track last tool to prevent consecutive update_tool calls
        
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
                print(f"{Colors.CYAN}Assistant: {Colors.RESET}", end="", flush=True)
            
            # Reset stream parser
            self.stream_parser.reset()
            
            # Stream the response
            try:
                with requests.post(self.api_url, headers=headers, json=payload, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        delta = self.stream_parser.process_line(line)
                        
                        if delta is None:
                            continue
                        
                        if delta.get('done'):
                            break
                        
                        # Print text only on first step
                        if step == 1:
                            text = self.stream_parser.handle_delta(delta)
                            if text:
                                print(text, end="", flush=True)
                        else:
                            # Process deltas silently on subsequent steps (agent is reasoning)
                            self.stream_parser.handle_delta(delta)
            
            except requests.exceptions.RequestException as e:
                print(f"\n{Colors.RED}[Error] API request failed: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}[Recovery] Retrying...\n{Colors.RESET}")
                if step < max_steps:
                    continue
                else:
                    return False
            
            if step == 1:
                print()  # Newline after first response
            
            # Process the result
            result = self.stream_parser.get_result()
            
            if result["type"] == "tool_calls":
                # Agent decided to use a tool
                tool_calls = result["tool_calls"]
                if not tool_calls:
                    print(f"{Colors.RED}[Error]: Failed to parse tool calls{Colors.RESET}")
                    return False
                
                # Add agent's tool use to conversation (empty content for tool-only messages)
                self.conversation.add_assistant_message("")
                
                # Execute the tools with step tracking
                print(f"\n{Colors.YELLOW}[Executing {len(tool_calls)} tool(s) at step {step}...]{Colors.RESET}\n")
                
                should_exit = False
                for i, tool_call in enumerate(tool_calls, 1):
                    tool_execution_count += 1
                    func_name = tool_call["function_name"]
                    args = tool_call["arguments"]
                    
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
                    
                    print(f"{Colors.YELLOW}[Tool {i}/{len(tool_calls)}]: {func_name}{Colors.RESET}")
                    print(f"  {Colors.CYAN}Args: {args}{Colors.RESET}")
                    
                    try:
                        tool_result, exit_flag = self.tool_manager.execute_tool(func_name, args)
                        
                        # Format and display the result (truncate if needed)
                        formatted_result = format_tool_result(tool_result, func_name)
                        result_display = truncate_text(tool_result, max_length=300)
                        print(f"  {Colors.YELLOW}Result: {result_display}{Colors.RESET}\n")
                        
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
                        print(f"  {Colors.RED}{error_msg}{Colors.RESET}\n")
                        self.conversation.add_tool_result(
                            tool_call_id=tool_call["id"],
                            function_name=func_name,
                            result=error_msg
                        )
                
                # If any tool requested exit, stop the loop
                if should_exit:
                    return True
                
                # Show reasoning prompt to encourage agent to think about next step
                if step == 1:
                    print(f"{Colors.CYAN}[Reasoning about tool results...]" + 
                          f" Agent will decide next action...{Colors.RESET}\n")
                
                # Loop continues - agent will reason about tool results and decide next action
                continue
            
            else:
                # Agent decided to respond with text
                self.conversation.add_assistant_message(result["content"])
                if tool_execution_count > 0:
                    print(f"{Colors.CYAN}[Task complete: Executed {tool_execution_count} tool(s) across {step} step(s)]{Colors.RESET}\n")
                return False
        
        # Max steps reached
        print(f"{Colors.YELLOW}[Warning]: Max agent steps reached ({max_steps}). Task may be incomplete.{Colors.RESET}")
        return False
