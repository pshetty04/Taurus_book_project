import requests
import re

# --- API Endpoints ---
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


def get_definition(word: str) -> str:
    """
    Fetches comprehensive definitions of a word and formats them.
    """
    try:
        response = requests.get(f"{DICTIONARY_API_URL}{word}")
        response.raise_for_status()
        
        data = response.json()[0]

        response_word = data.get('word', '').lower()
        if response_word != word.lower():
            return f"Sorry, I couldn't find a precise match for '{word}'. Did you mean '{response_word}'?"

        phonetic = data.get('phonetic', '')
        output = [f"**{word.capitalize()}** *({phonetic})*"]
        
        for i, meaning in enumerate(data.get('meanings', [])):
            part_of_speech = meaning.get('partOfSpeech', '')
            definition_text = meaning['definitions'][0]['definition']
            output.append(f"\n{i+1}. *({part_of_speech})* {definition_text}")
        
        return "\n".join(output)

    except requests.exceptions.HTTPError:
        return f"Sorry, I couldn't find a definition for '{word}'. Please check the spelling."
    except Exception as e:
        print(f"Dictionary Error: {e}")
        return "An unexpected error occurred while fetching the definition."


def get_book_info(book_title: str) -> str:
    """
    Fetches the description (plot summary) of a book from the Google Books API.
    """
    params = {"q": f"intitle:{book_title}", "maxResults": 1}
    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "items" not in data or not data["items"]:
            return f"Sorry, I couldn't find any information for the book '{book_title}'."
            
        book_info = data["items"][0]["volumeInfo"]
        title = book_info.get("title", "N/A")
        authors = ", ".join(book_info.get("authors", ["Unknown"]))
        description = book_info.get("description", "No plot summary available.")

        return f"**{title}** by {authors}\n\n**Plot Summary:**\n{description}"

    except Exception as e:
        print(f"Google Books Error: {e}")
        return "An unexpected error occurred while fetching book information."


def answer(prompt: str) -> str:
    """
    **NEW and IMPROVED**
    Uses regular expressions to flexibly understand user intent and extract keywords,
    ignoring punctuation.
    """
    prompt_lower = prompt.lower().strip()

    # --- Regex Patterns to understand different ways of asking ---
    # It looks for trigger words and then captures the subject of the question.
    define_pattern = r"(?:what is|what's|what is the meaning of|define|meaning of)\s+['\"]?([\w\s-]+)['\"]?"
    plot_pattern = r"(?:plot of|summary of|what is the plot of|what's the plot of)\s+['\"]?(.+?)['\"]?"

    # --- Match against patterns ---
    define_match = re.search(define_pattern, prompt_lower)
    plot_match = re.search(plot_pattern, prompt_lower)

    if define_match:
        word = define_match.group(1).strip().rstrip('?.!')
        if word:
            return get_definition(word)

    if plot_match:
        title = plot_match.group(1).strip().rstrip('?.!')
        if title:
            return get_book_info(title)
        
    # --- Default Case ---
    return (
        "I can help with a couple of things:\n\n"
        "1.  **Definitions:** Try asking `What is melancholy?`\n"
        "2.  **Book Plots:** Try asking `Plot of The Great Gatsby`\n\n"
        "How can I assist you?"
    )