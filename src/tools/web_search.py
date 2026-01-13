"""Web search tool - allows agent to search for information online"""
from typing import Dict, Tuple
import requests
from urllib.parse import quote

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the internet for information about packages, troubleshooting, or technical topics. Use this when you need current information about Python packages, compatibility issues, installation problems, or general technical questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'pandas python package installation', 'openpyxl excel compatibility', 'python requests module')"
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search: 'general' for general web search, 'package' for Python package info, 'error' for error troubleshooting",
                    "enum": ["general", "package", "error"]
                }
            },
            "required": ["query"]
        }
    }
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    """Execute web search and return results"""
    query = str(args.get("query", "")).strip()
    search_type = str(args.get("search_type", "general")).strip()
    
    if not query:
        return "Error: Search query cannot be empty", False
    
    try:
        # Enhance query based on search type
        if search_type == "package":
            # Search for Python package information
            enhanced_query = f"{query} python package pypi documentation"
        elif search_type == "error":
            # Search for error solutions
            enhanced_query = f"{query} solution fix python"
        else:
            enhanced_query = query
        
        # Build Google search URL
        search_url = f"https://www.google.com/search?q={quote(enhanced_query)}"
        
        # Try to fetch search results using DuckDuckGo API as fallback (more reliable for automation)
        try:
            search_results = _search_duckduckgo(query, search_type)
            if search_results:
                return f"Search Results for '{query}':\n\n{search_results}", False
        except:
            pass
        
        # If DuckDuckGo fails, return Google search URL
        result = (
            f"Search URL for '{query}':\n"
            f"{search_url}\n\n"
            f"Unable to fetch live results, but you can check the URL above in a browser.\n"
            f"Key terms to look for: installation, compatibility, documentation, PyPI"
        )
        return result, False
        
    except Exception as e:
        return f"Error during search: {str(e)}", False


def _search_duckduckgo(query: str, search_type: str) -> str:
    """Try to get search results from DuckDuckGo API"""
    try:
        # Enhance query
        if search_type == "package":
            enhanced_query = f"{query} python package pypi"
        elif search_type == "error":
            enhanced_query = f"{query} python solution fix"
        else:
            enhanced_query = query
        
        # DuckDuckGo API endpoint
        url = "https://api.duckduckgo.com/"
        params = {
            "q": enhanced_query,
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant results
            results = []
            
            # Add abstract if available
            if data.get("Abstract"):
                results.append(f"Summary: {data['Abstract']}")
            
            # Add related topics
            if data.get("RelatedTopics"):
                results.append("\nRelated Topics:")
                for topic in data["RelatedTopics"][:3]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        text = topic["Text"][:150]  # Truncate to 150 chars
                        results.append(f"  • {text}")
            
            if results:
                return "\n".join(results)
        
        return None
    except:
        return None
