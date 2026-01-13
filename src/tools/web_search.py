"""Web search tool - allows agent to search for information online using DuckDuckGo via LangChain"""
from typing import Dict, Tuple
import requests
try:
    from langchain_community.tools import DuckDuckGoSearchRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the internet for current information about Python packages, troubleshooting, compatibility issues, or technical topics. Use this when encountering unknown packages, compatibility errors, or need up-to-date documentation and solutions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'pandas python package installation', 'openpyxl excel compatibility with python', 'how to read xlsx files python 2025')"
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search: 'general' for general web search, 'package' for Python package info, 'error' for error troubleshooting, 'docs' for documentation",
                    "enum": ["general", "package", "error", "docs"]
                }
            },
            "required": ["query"]
        }
    }
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    """Execute web search using LangChain's DuckDuckGo or fallback"""
    query = str(args.get("query", "")).strip()
    search_type = str(args.get("search_type", "general")).strip()
    
    if not query:
        return "Error: Search query cannot be empty", False
    
    try:
        # Enhance query based on search type for better results
        if search_type == "package":
            enhanced_query = f"{query} python package pypi pip install"
        elif search_type == "error":
            enhanced_query = f"{query} python solution error fix troubleshoot"
        elif search_type == "docs":
            enhanced_query = f"{query} documentation official API"
        else:
            enhanced_query = query
        
        # Use LangChain if available
        if LANGCHAIN_AVAILABLE:
            try:
                search_engine = DuckDuckGoSearchRun(
                    max_results=5  # Return top 5 results
                )
                results = search_engine.run(enhanced_query)
                
                if results and results.strip():
                    return (
                        f"Search Results for: {query}\n"
                        f"{'='*60}\n\n"
                        f"{results}\n\n"
                        f"{'='*60}\n"
                        f"Note: These are the most relevant results from the web. "
                        f"Look for installation instructions, compatibility notes, or solutions."
                    ), False
                else:
                    return (
                        f"No results found for '{query}'. "
                        f"Try rephrasing your query or searching for related topics."
                    ), False
                    
            except Exception as e:
                # Fallback to URL if LangChain fails
                return _fallback_search(query, enhanced_query, str(e))
        else:
            return _fallback_search(query, enhanced_query, "LangChain not installed")
        
    except Exception as e:
        return f"Error during search: {str(e)}", False


def _fallback_search(query: str, enhanced_query: str, error_msg: str) -> Tuple[str, bool]:
    """Fallback search using requests library"""
    try:
        # Try to get results from DuckDuckGo API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": enhanced_query,
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Add abstract if available
            if data.get("AbstractText"):
                results.append(f"Summary:\n{data['AbstractText']}\n")
            
            # Add related topics
            if data.get("RelatedTopics"):
                results.append("Related Information:")
                for topic in data["RelatedTopics"][:5]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        text = topic["Text"][:200]
                        if topic.get("FirstURL"):
                            results.append(f"  - {text}\n    Link: {topic['FirstURL']}")
                        else:
                            results.append(f"  - {text}")
            
            if results:
                return (
                    f"Search Results for: {query}\n"
                    f"{'='*60}\n\n"
                    f"{''.join(results)}\n\n"
                    f"{'='*60}\n"
                    f"Note: Using fallback search. Results should be relevant to your query."
                ), False
        
        # If API fails, return helpful message
        return (
            f"Could not fetch live search results (reason: {error_msg})\n\n"
            f"However, for '{query}', you might want to check:\n"
            f"  - PyPI.org - for Python packages\n"
            f"  - Official documentation of the package\n"
            f"  - Stack Overflow or GitHub issues\n"
            f"  - Package compatibility matrices\n\n"
            f"Try rephrasing your query or search manually on these resources."
        ), False
        
    except Exception as e:
        return (
            f"Error fetching search results: {str(e)}\n\n"
            f"Suggestions:\n"
            f"  - Check your internet connection\n"
            f"  - Try a simpler search query\n"
            f"  - Look for the package documentation online"
        ), False
        
        return None
    except:
        return None
