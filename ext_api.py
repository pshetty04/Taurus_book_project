import os
import functools
from dotenv import load_dotenv
from serpapi import SerpApiClient
import requests
from urllib.parse import urlparse, parse_qs, unquote

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_API = "https://www.googleapis.com/books/v1/volumes?q="
TIMEOUT = 90

@functools.lru_cache(maxsize=1024)
def lookup_google(book_query, max_results=5):
    """Fetches book data from the Google Books API."""
    url = f"{GOOGLE_API}{book_query}&maxResults={max_results}&printType=books"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        books = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            books.append({
                "title": info.get("title", "Unknown Title"),
                "authors": ", ".join(info.get("authors", ["Unknown Author"])),
                "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
            })
        return books
    except requests.exceptions.RequestException as e:
        print(f" Google API Error: {e}")
        return []

def get_shopping_results(book_title):
    """Gets Google Shopping results and processes them into a clean, consistent format."""
    if not SERPAPI_API_KEY: return []
    params = {
        "api_key": SERPAPI_API_KEY, "engine": "google_shopping",
        "q": f"{book_title} book", "google_domain": "google.co.in",
        "gl": "in", "hl": "en"
    }
    try:
        client = SerpApiClient(params)
        data = client.get_dict()
        if "shopping_results" not in data: return []
        
        final_results = []
        # **THE FIX**: Process the raw results from the API into our standard format.
        for item in data["shopping_results"]:
            # Use the direct product link from the API
            final_link = item.get("product_link", item.get("link", "#"))

            final_results.append({
                "title": item.get("title", "N/A"),
                "price": item.get("price", "N/A"),
                "seller": item.get("source", "N/A"), # Map 'source' to our 'seller' key
                "link": final_link
            })
        print(f"✅ Found and processed {len(final_results)} results from Google Shopping.")
        return final_results
    except Exception as e:
        print(f" Google Shopping Scraper Error: {e}")
        return []

def get_amazon_result(book_title):
    """Uses Google's standard search with a 'site:amazon.in' filter."""
    if not SERPAPI_API_KEY: return []
    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "q": f"site:amazon.in {book_title} book",
        "gl": "in", "hl": "en"
    }
    try:
        client = SerpApiClient(params)
        data = client.get_dict()
        all_results = data.get("organic_results", [])
        if not all_results: return None

        top_result = all_results[0]
        price = top_result.get("rich_snippet", {}).get("top", {}).get("detected_extensions", [{}])[0].get("price")
        
        result = {
            "title": top_result.get("title", "N/A"),
            "price": price or "See site",
            "link": top_result.get("link", "#")
        }
        print("✅ Found an Amazon result via Google site search.")
        return result
    except Exception as e:
        print(f"Amazon (via Google) Search Error: {e}")
        return None