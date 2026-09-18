from zoneinfo import ZoneInfo
from datetime import datetime
import re
import wikipedia
from bs4 import BeautifulSoup
import requests

def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a given timezone.
    Use this when the user asks what time it is, or mentions any timezone.
    
    Args:
        timezone: A valid timezone string like 'UTC', 'America/New_York', 'Asia/Tokyo'
    """
    try:
        dt = datetime.now(ZoneInfo(timezone))
        return dt.strftime("%Y-%m-%d %H:%M %Z")
    except Exception as e:
        return f"Error: Invalid timezone '{timezone}'. {str(e)}"


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Use this when the user asks for any calculation, math problem, or numeric operation.
    Only supports +, -, *, /, **, and parentheses.
    
    Args:
        expression: A math expression as a string, e.g. "145 * 23" or "(10 + 5) / 3"
    """
    if not re.match(r'^[\d\s\.\+\-\*\/\(\)]+$', expression):
        return "Error: Invalid characters. Only numbers and + - * / ** ( ) . are allowed."
    
    try:
        # Safe eval
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: Could not evaluate. {str(e)}"


def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for a topic and return a short summary.
    Use this when the user asks about a person, place, event, concept, or 
    anything that requires factual knowledge you don't already have.
    
    Args:
        query: The search term, e.g. "lightbulb inventor" or "Python programming language"
    """
    try:
        wikipedia.set_lang("en")
        page = wikipedia.page(query, auto_suggest=True)

        return f"{page.title}: {page.summary[:600]}"
    except wikipedia.exceptions.DisambiguationError as e:
        
        try:
            page = wikipedia.page(e.options[0])
            return f"{page.title}: {page.summary[:600]}"
        except:
            return f"Error: '{query}' is ambiguous. Be more specific."
    except wikipedia.exceptions.PageError:
        return f"Error: No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Error: {str(e)}"
    
    
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    Use this when the user asks about weather, temperature, rain, or conditions.
    
    Args:
        city: City name, e.g. "Tokyo", "Paris", "New York"
    """
    # Mock data for learning purposes
    weather_db = {
        "tokyo": "24°C, Clear sky, Wind: 12 km/h NE, Humidity: 65%",
        "paris": "18°C, Partly cloudy, Wind: 8 km/h SW, Humidity: 72%",
        "new york": "22°C, Sunny, Wind: 15 km/h NW, Humidity: 55%",
        "london": "16°C, Light rain, Wind: 10 km/h E, Humidity: 80%",
    }
    
    key = city.lower().replace(", japan", "").replace(", france", "").replace(", uk", "").strip()
    result = weather_db.get(key)
    
    if result:
        return f"Weather in {city}: {result}"
    else:
        # Return a clear error so the LLM knows the tool failed, not the user
        return f"Error: Weather data not available for '{city}'. Available cities: Tokyo, Paris, New York, London."
    