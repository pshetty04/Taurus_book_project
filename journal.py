# pages/journal.py

import streamlit as st
import pandas as pd
import datetime as dt
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db/journal.db"
DB_PATH.parent.mkdir(exist_ok=True, parents=True)

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS journal_entries (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, book TEXT,
                   rating REAL, summary TEXT, date_written TEXT
               )"""
        )
init_db()

def render_page():
    st.header("My Reading Journal")

    with st.form("new_entry"):
        st.subheader("New entry")
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.number_input("User ID", min_value=1, step=1)
        with col2:
            book = st.text_input("Book title")
        rating = st.slider("Rating", 0.0, 5.0, 3.0, 0.5)
        summary = st.text_area("Your thoughts (optional)")
        submitted = st.form_submit_button("Save entry", type="primary")

        if submitted:
            if not book:
                st.error("Please enter a book title.")
            else:
                with get_conn() as conn:
                    conn.execute(
                        "INSERT INTO journal_entries (user_id, book, rating, summary, date_written) VALUES (?, ?, ?, ?, ?)",
                        (user_id, book.strip(), rating, summary.strip(), dt.datetime.now().isoformat(timespec="seconds"))
                    )
                st.success("Entry saved!")
    
    st.divider()
    st.subheader("Past entries")
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM journal_entries ORDER BY date_written DESC", conn)

    if df.empty:
        st.info("No journal entries yet.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['book']}  |  ⭐ {row['rating']}  |  {row['date_written']}"):
                st.write(row["summary"] or "*(no summary)*")