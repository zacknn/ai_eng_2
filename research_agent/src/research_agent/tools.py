from smolagents import tool
from ddgs import DDGS

@tool
def get_search_results_as_string(query: str, num_results: int = 5) -> str:
    """
    Performs a search and returns the formatted results as a single string.
    
    Args:
        query (str): The search query.
        num_results (int): The number of search results to return. Default is 5.
    """
    output = []
    
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=num_results)
        
        for i, r in enumerate(results, 1):
            # Format each result cleanly
            item_str = (
                f"[{i}] {r.get('title')}\n"
                f"URL: {r.get('href')}\n"
                f"Summary: {r.get('body')}\n"
                f"{'-'*40}"
            )
            output.append(item_str)
            
    # Join all results together with double newlines
    return "\n\n".join(output)


