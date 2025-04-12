import streamlit as st

get_movies = st.Page("get_movies.py", title="Download Movie", icon=":material/add_circle:")
manage_downloads = st.Page("manage_downloads.py", title="Manages Downloads", icon=":material/delete:")

pg = st.navigation([get_movies, manage_downloads])

st.set_page_config(
    page_title="Movie Downloader to Plex", 
    layout="wide")

pg.run()