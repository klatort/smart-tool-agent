"""Environment configuration and constants"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
MODEL_ID = os.getenv("MODEL_ID")

# --- Agent Configuration ---
# Safety threshold: Number of steps before asking user to continue
# Set to 0 or negative to disable (infinite steps without confirmation)
AGENT_SAFETY_THRESHOLD = int(os.getenv("AGENT_SAFETY_THRESHOLD", "20"))

# Check interval: How often to ask after threshold is exceeded (every N steps)
AGENT_CHECK_INTERVAL = int(os.getenv("AGENT_CHECK_INTERVAL", "10"))

# Memory consolidation settings
AGENT_CONSOLIDATION_TURNS = int(os.getenv("AGENT_CONSOLIDATION_TURNS", "10"))
AGENT_CONSOLIDATION_MESSAGES = int(os.getenv("AGENT_CONSOLIDATION_MESSAGES", "15"))
AGENT_CONSOLIDATION_CONTEXT_SIZE = int(os.getenv("AGENT_CONSOLIDATION_CONTEXT_SIZE", "50000"))

# --- ANSI Color Codes ---
class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
