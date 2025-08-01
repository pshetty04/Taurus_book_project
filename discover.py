# pages/discover.py

import streamlit as st
from backend.ext_api import lookup_google, get_shopping_results, get_amazon_result

def render_page():
    st.header(" Discover & Compare Prices")
    st.write("Search for a book, select the correct edition, and see where you can buy it online.")
    
    search_query = st.text_input("Enter a book title to search:", placeholder="e.g., The Alchemist")

    if search_query:
        st.divider()
        with st.spinner("Searching Google Books..."):
            google_results = lookup_google(search_query)

        if not google_results:
            st.error("Could not find any books matching that query on Google Books. Please try again.")
        else:
            st.subheader("Step 1: Choose the correct book from the list")
            cols = st.columns(min(len(google_results), 5))
            for i, book in enumerate(google_results[:5]):
                with cols[i]:
                    if book.get("thumbnail"): st.image(book["thumbnail"])
                    st.caption(book["title"])
                    if st.button("Find Prices", key=f"book_{i}", help=f"Find prices for {book['title']}"):
                        st.session_state.selected_book_discover = book # Use a unique session state key
    
    if 'selected_book_discover' in st.session_state:
        selected = st.session_state.selected_book_discover
        with st.spinner(f"Searching online stores for '{selected['title']}'..."):
            amazon_result = get_amazon_result(selected['title'])
            shopping_results = get_shopping_results(selected['title'])
        
        st.divider()
        st.subheader(f"Step 2: Buying options for '{selected['title']}'")
        
        st.markdown("#### 🛒 Amazon.in")
        if amazon_result:
            st.write(f"**{amazon_result['price']}** - [{amazon_result['title']}]({amazon_result['link']})")
        else:
            st.info("No relevant listing found on Amazon.in for this book.")
        
        st.markdown("---")
        st.markdown("####  Other Online Stores")
        if not shopping_results:
            st.warning("No listings found on other major online stores.")
        else:
            for item in shopping_results:
                if "amazon" in item['seller'].lower():
                    continue
                st.write(f"**{item['seller']}**: {item['price']} - [{item['title']}]({item['link']})")