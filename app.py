# app.py

import streamlit as st
import pickle
import joblib
import pandas as pd
from pathlib import Path
import base64

# Import all necessary backend functions for all pages
from recommender_utils import (
    recommend_books_by_filter_api, 
    recommend_similar_books_local, 
    get_trending_books
)
from backend.ext_api import lookup_google, get_amazon_result, get_shopping_results
from backend.p_chatbot import answer
from pages import discover, chatbot, journal

# --- Page Configuration (only here in app.py) ---
st.set_page_config(page_title="Taurus", layout="wide",initial_sidebar_state="collapsed")
@st.cache_data
def get_image_as_base64(path):
    """Reads an image file and returns it as a Base64 encoded string."""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# In app.py

st.markdown("""
<style>
/* 1. Main Background: Rectangular vignette effect */
[data-testid="stAppViewContainer"] {

background-image: radial-gradient(ellipse at center,#6f4e37 0%, #211717 100%);
}


/* 2. Navigation Button Text */
div[data-testid="stHorizontalBlock"] button p {
    color: #4A2C2A !important;
}
div[data-testid="stTextInput"] input {
color: #311D06; /* A dark, readable brown */
}
div[data-testid="stTextInput"] input {
    background-color: transparent !important; /* Makes the inner field transparent */
    color: #311D06 !important; }
/* This targets the text the user types into the chat input box */

div[data-testid="stChatInput"] textarea {
background-color: #D2B48C !important;
color: #311D06 !important; 
}
div[data-testid="stNumberInput"] input {
        background-color: #D2B48C !important;
        color: #311D06 !important;}
/* 4. Dropdown Menu Options (when the list is open) */
li[data-baseweb="select-option"] > div,
div[role="listbox"] li {
    color: #3D2B1F !important;
}

/* 5. Selected Item in the Dropdown Box (when closed) */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    color: #3D2B1F !important; /* Dark brown text */
}

/* 6. Hide the default sidebar */
[data-testid="stSidebar"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

def display_star_rating(rating: float, max_rating: int = 10) -> str:
    if rating is None or pd.isna(rating): return "Not Rated"
    rating_on_5 = (rating / max_rating) * 5
    num_stars = int(round(rating_on_5))
    stars_str = "⭐" * num_stars + "☆" * (5 - num_stars)
    return f"{stars_str} ({rating:.1f}/{max_rating})"

def display_book_image(url: str | None, width: int = 120):
    if url and "http" in url:
        st.image(url, width=width)
    else:
        st.markdown(f'<div style="width:{width}px; height:180px; display:flex; align-items:center; justify-content:center; border:1px solid #ddd; background-color:#f9f9f9; color:#aaa;">No Image</div>', unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(show_spinner="Loading all book data…")
def load_all_data():
    data_dir = Path(__file__).resolve().parent / "data"
    df_meta, cosine_sim, indices, final_ratings, genre_list = None, None, None, None, []
    try:
        with open(data_dir / "df_meta.pkl", "rb") as f: df_meta = pickle.load(f)
        with open(data_dir / "indices.pkl", "rb") as f: indices = pickle.load(f)
        cosine_sim = joblib.load(data_dir / "cosine_sim.joblib")
        final_ratings_pkl_path = data_dir / "final_ratings.pkl"
        if final_ratings_pkl_path.exists():
            with open(final_ratings_pkl_path, "rb") as f: final_ratings = pickle.load(f)
        all_genres = df_meta['Genres'].dropna().str.split(', ').explode()
        genre_list = sorted(all_genres.str.strip().unique())
    except Exception as e:
        st.error(f"Error loading local data files: {e}")
    return df_meta, cosine_sim, indices, final_ratings, genre_list

# --- Main App Logic ---

# Landing Page
if 'app_started' not in st.session_state: st.session_state.app_started = False
if not st.session_state.app_started:
    try:
        img_base64 = get_image_as_base64("landing.png")

        # Define the full-screen background CSS
        page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] > .main {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Hide the header and Streamlit branding */
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none;
            visibility: hidden;
        }}
        
        /* Style and position the button */
        div.stButton > button {{
            position: fixed;
            bottom: 10vh; /* 10% from the bottom */
            left: 50%;
            transform: translateX(-50%);
            padding: 1rem 2rem;
            font-size: 1.5rem;
            border-radius: 10px;
            border: 3px solid #C69533;     /* Dark brown border */
            background-color: #E3B778;     /* Tan background */
            color: #311D06; 
            transition: all 0.2s ease-in-out; /* Smooth transition */
        }}

        /* --- NEW: Hover state for the button --- */
        div.stButton > button:hover {{
            background-color: #C69533; /* Slightly darker tan */
            border-color:#8B4513;
            color: #FFFFFF
        }}

        /* --- NEW: Active/Click state for the button --- */
        div.stButton > button:active {{
            background-color:#C1A784;  /* Even darker tan when clicked */
        }}
        </style>
        """ 
        st.markdown(page_bg_img, unsafe_allow_html=True)
        if st.button("Enter the Library",type="primary"):
            st.session_state.app_started = True
            st.rerun()
    except Exception:
        # Fallback if the image fails to load
        st.title("Welcome to Taurus")
        if st.button("Enter", use_container_width=True):
            st.session_state.app_started = True
            st.rerun()
    

else: 
    df_meta, cosine_sim, indices_map, final_ratings, genre_list = load_all_data()
    
    # Restored styled text title
    st.markdown("""
        <h1 style="font-size: 56px; font-weight: bold; text-align: center; color: #FAF3E0;
                   text-shadow: 2px 2px 3px #111111, 4px 4px 5px rgba(0,0,0,0.5);">
            Taurus
        </h1>
    """, unsafe_allow_html=True)
    
    if 'page' not in st.session_state: st.session_state.page = "Recommender"
    cols = st.columns(5)
    if cols[0].button("Recommender", use_container_width=True): st.session_state.page = "Recommender"
    if cols[1].button("Trending", use_container_width=True): st.session_state.page = "Trending"
    if cols[2].button("Discover", use_container_width=True): st.session_state.page = "Discover"
    if cols[3].button("Chatbot", use_container_width=True): st.session_state.page = "Chatbot"
    if cols[4].button("Journal", use_container_width=True): st.session_state.page = "Journal"
    st.divider()
    
    # --- Page Content Router ---
    if st.session_state.page == "Recommender":
        st.header("Book Recommender")
        if df_meta is None:
            st.error("Could not load local data files required for this feature.")
        else:
            tab1, tab2 = st.tabs(["Find Similar Books (using Local Data)", "Find Books by Filter (using Live API)"])
            with tab1:
                st.subheader("Get recommendations based on a book you like")
                title_input = st.text_input("Enter a book title (e.g., The Hobbit)")
                top_n_similar = st.number_input("Number of similar books", 1, 10, 5, key="top_n_similar")
                if st.button("Find Similar Books", type="primary"):
                    with st.spinner("Finding similar books and fetching fresh details..."):
                        similar_books_df = recommend_similar_books_local(
                            input_title=title_input, df_meta=df_meta, cosine_sim=cosine_sim, indices=indices_map, top_n=top_n_similar
                        )
                    st.divider()
                    if not similar_books_df.empty:
                        st.subheader(f"Books similar to '{title_input}':")
                        for index, row in similar_books_df.iterrows():
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                display_book_image(row.get("Image-URL"))
                            with col2:
                                st.subheader(row["Book-Title"])
                                st.caption(f"By {row['Book-Author']}")
                    else:
                        st.warning("Could not find that book or any similar ones. Please try a more specific title.")
            with tab2:
                st.subheader("Search for popular books by filter")
                genre  = st.text_input("Genre", key="genre_filter")
                author = st.text_input("Author", key="author_filter")
                year   = st.slider("Publication Year Range", 1800, 2025, (1990, 2020))
                top_n_filter = st.number_input("Number of results", 1, 10, 5, key="top_n_filter")
                if st.button("Find Books by Filter"):
                    with st.spinner("Searching for books..."):
                        results_df = recommend_books_by_filter_api(genre=genre, author=author, year_range=year, top_n=top_n_filter)
                    st.divider()
                    if not results_df.empty:
                        st.subheader("API Search Results:")
                        for index, row in results_df.iterrows():
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                display_book_image(row.get("Image-URL"))
                            with col2:
                                st.subheader(row["Book-Title"])
                                st.caption(f"By {row['Book-Author']} ({row.get('Published-Year', '')})")
                    else:
                        st.warning("No books found for this combination via the API.")

    # In app.py, replace the whole "Trending" section

    elif st.session_state.page == "Trending":
        st.header("🔥 Trending Books by Genre")
        if final_ratings is None:
            st.error("Trending Data Not Available. This feature requires the `final_ratings.pkl` file.")
        else:
            st.write("Discover the highest-rated books in your favorite genres based on user reviews.")
        
        # --- INPUT WIDGETS ---
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_genre = st.selectbox("Select a Genre", genre_list, key="genre_select")
            with col2:
                top_n_trending = st.number_input("Show Top", 1, 10, 3, key="top_n_trending")

        # **FIX**: The second, duplicate st.selectbox was removed from here.
        
        # The logic now runs automatically if a genre is selected.
            if selected_genre:
                with st.spinner(f"Finding trending books in {selected_genre}..."):
                    trending_books = get_trending_books(
                    genre=selected_genre, 
                    df_meta=df_meta, 
                    final_ratings=final_ratings, 
                    top_n=top_n_trending # **FIX**: Now uses the value from the number input
                )
                st.divider()
                if not trending_books.empty:
                    st.subheader(f"Top {len(trending_books)} Trending Books in {selected_genre}")
                    for index, row in trending_books.iterrows():
                        col1_disp, col2_disp = st.columns([1, 3])
                        with col1_disp:
                            display_book_image(row.get("Image-URL"))
                        with col2_disp:
                            st.subheader(row["Book-Title"])
                            st.caption(f"By {row['Book-Author']}")
                            st.markdown(f"**Rating:** {display_star_rating(row['avg_rating'])}")
                            st.caption(f"Based on {int(row['num_ratings'])} user reviews.")
                        st.write("---")
                else:
                    st.warning(f"No trending books with enough ratings found for '{selected_genre}'.")

    elif st.session_state.page == "Discover":
        # This now correctly calls your discover.py file
        discover.render_page()

    elif st.session_state.page == "Chatbot":
        # This now correctly calls your chatbot.py file
        chatbot.render_page()

    elif st.session_state.page == "Journal":
        # This now correctly calls your journal.py file
        journal.render_page()