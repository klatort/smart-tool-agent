"""Environment configuration and constants"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
MODEL_ID = os.getenv("MODEL_ID")

# --- ANSI Color Codes ---
class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
