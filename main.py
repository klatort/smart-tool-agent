# Current time: 2026-01-12 18:38:02
# Last modified: 2026-01-12 18:24:06
"""
Living CLI Agent - Main Entry Point
"""
import sys
from src.config import API_KEY, API_URL, MODEL_ID, Colors
from src.agent import Agent


def main():
    """Entry point for the Living CLI Agent"""
    # Validate configuration
    if not API_KEY or not API_URL or not MODEL_ID:
        print(f"{Colors.RED}Error: Missing environment variables in .env file{Colors.RESET}")
        print("Required: API_KEY, API_URL, MODEL_ID")
        sys.exit(1)
    
    # Create and run agent
    agent = Agent(api_key=API_KEY, api_url=API_URL, model_id=MODEL_ID)
    agent.run()


if __name__ == "__main__":
    main()