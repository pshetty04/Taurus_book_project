# recommender_utils.py

import requests
import pandas as pd
from difflib import get_close_matches
import streamlit as st # Import Streamlit for caching

# --- API-based functions ---

@st.cache_data(ttl="6h") # Cache API results for 6 hours
def fetch_book_details_from_api(book_title: str) -> dict | None:
    """
    **NEW**: Fetches fresh details (like a working image URL) for a single book title.
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f'intitle:"{book_title}"', "maxResults": 1, "printType": "books", "langRestrict": "en"}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if "items" in data:
            info = data["items"][0].get("volumeInfo", {})
            return {
                "Book-Title": info.get("title", book_title),
                "Book-Author": ", ".join(info.get("authors", ["N/A"])),
                "Published-Year": info.get("publishedDate", "N/A")[:4],
                "Image-URL": info.get("imageLinks", {}).get("thumbnail")
            }
    except Exception as e:
        print(f"API request failed for '{book_title}': {e}")
    return None

def recommend_books_by_filter_api(genre=None, author=None, year_range=None, top_n=5):
    """Finds books using the Google Books API. (This function is already API-based and works well)."""
    base_url = "https://www.googleapis.com/books/v1/volumes"
    query_parts = []
    if author: query_parts.append(f"inauthor:{author.strip()}")
    if genre: query_parts.append(f"subject:{genre.strip()}")
    if not query_parts: query_parts.append("subject:fiction")
    query = "+".join(query_parts)
    params = {"q": query, "maxResults": 40, "printType": "books"}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        books = []
        if "items" in data:
            for item in data.get("items", []):
                info = item.get("volumeInfo", {})
                published_date = info.get("publishedDate", "0")
                try:
                    year = int(published_date[:4])
                    if year_range and not (year_range[0] <= year <= year_range[1]):
                        continue
                except (ValueError, TypeError):
                    continue
                if all(k in info for k in ["title", "authors", "imageLinks"]):
                    books.append({
                        "Book-Title": info.get("title"), "Book-Author": ", ".join(info.get("authors", ["N/A"])),
                        "Published-Year": year, "Image-URL": info.get("imageLinks", {}).get("thumbnail"),
                    })
        return pd.DataFrame(books).drop_duplicates(subset="Book-Title").head(top_n)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return pd.DataFrame()

# --- Local data-based functions (now enriched with API calls) ---

def get_best_book_match(query_title: str, candidate_titles: list, cutoff: float = 0.5) -> str | None:
    if not query_title: return None
    matches = get_close_matches(query_title.lower(), [str(t).lower() for t in candidate_titles], n=1, cutoff=cutoff)
    if not matches: return None
    for title in candidate_titles:
        if str(title).lower() == matches[0]:
            return title
    return None

def recommend_similar_books_local(input_title, df_meta, cosine_sim, indices, top_n=5):
    """
    **MODIFIED**: Finds similar book titles locally, then fetches their details from the API.
    """
    if not input_title: return pd.DataFrame()
    
    unique_titles = df_meta['Book-Title'].unique()
    matched_title = get_best_book_match(input_title, list(unique_titles))
    if not matched_title: return pd.DataFrame()

    idx = indices[matched_title].iloc[0] if isinstance(indices[matched_title], pd.Series) else indices[matched_title]
    sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_n+10]
    book_indices = [i[0] for i in sim_scores]
    
    recommended_books = df_meta.iloc[book_indices].drop_duplicates(subset=['Book-Title']).head(top_n)

    # **NEW**: Fetch fresh details for each recommended book to get working images
    fresh_details = [fetch_book_details_from_api(title) for title in recommended_books['Book-Title']]
    return pd.DataFrame([details for details in fresh_details if details is not None])

def get_trending_books(genre: str, df_meta: pd.DataFrame, final_ratings: pd.DataFrame, top_n: int = 3):
    """
    **MODIFIED**: Finds top trending titles locally, then fetches their details from the API.
    """
    if 'Genres' not in df_meta.columns: return pd.DataFrame()
    genre_books = df_meta[df_meta['Genres'].str.contains(genre, case=False, na=False)]
    if genre_books.empty: return pd.DataFrame()
    
    rated_books = final_ratings[final_ratings['Book-Title'].isin(genre_books['Book-Title'].unique())]
    rated_books = rated_books[rated_books['Book-Rating'] > 0]
    if rated_books.empty: return pd.DataFrame()

    rating_summary = rated_books.groupby('Book-Title').agg(avg_rating=('Book-Rating', 'mean'), num_ratings=('Book-Rating', 'count')).reset_index()
    
    top_books_df = rating_summary[rating_summary['num_ratings'] >= 20].sort_values(by='avg_rating', ascending=False).head(top_n)
    if top_books_df.empty: return pd.DataFrame()

    # **NEW**: Fetch fresh details for each trending book
    fresh_details = []
    for _, row in top_books_df.iterrows():
        details = fetch_book_details_from_api(row['Book-Title'])
        if details:
            details['avg_rating'] = row['avg_rating']
            details['num_ratings'] = row['num_ratings']
            fresh_details.append(details)
            
    return pd.DataFrame(fresh_details)