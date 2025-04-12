import streamlit as st
import requests
import os

from qbittorrent import Client # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html
from config import TORRENT_FILES_DIR
from config import LETTERBOX_USERNAME
from config import LETTERBOX_WATCHLIST_MAX_ITEMS


# Cache the function to avoid re-running it unnecessarily
@st.cache_data(show_spinner=False, ttl=3600)
def search_imdb(search_query: str) -> dict:
    
    # Format the API URL with the search query
    api_url = f"https://v3.sg.media-imdb.com/suggestion/x/{search_query.strip().replace(' ', '%20')}.json"
    response = requests.get(api_url)
    if response.status_code == 200:
        try:
            search_results = response.json()
            movies = []
            for result in search_results.get("d", []):
                if result.get("qid") == "movie":
                    imdb_id = result.get("id", "Unknown ID")
                    yts_details = get_yts_movie_details(imdb_id, with_images=True, with_cast=True)
                    movies.append({
                        "imdb_id": imdb_id,
                        "title": result.get("l", "Unknown Title"),
                        "year": result.get("y", "Unknown Year"),
                        "image": result.get("i", {}),
                        "yts_details": yts_details if yts_details else None
                    })
            
        except ValueError:
            st.error("Failed to parse the API response.")
    else:
        st.error(f"API request failed with status code {response.status_code}.")
        
    return movies

@st.fragment
def diplay_search_results(movies):
    """
    Display search results with checkboxes for downloading torrents.
    """
    with st.form("search_form"):
        st.markdown("## Search Results")
        selected_movies = []  # List to store selected movies for download

        for movie in movies:
            image_url = movie.get("image", {}).get("imageUrl", "")
            imdb_id = movie.get("imdb_id", "Unknown ID")
            title = movie.get("title", "Unknown Title")
            year = movie.get("year", "Unknown Year")
            col1, col2 = st.columns([4, 1])
            st.divider()
            with col1:
                st.write(f"**{title}** ({year})")
                if image_url:
                    st.image(image_url, width=100)
            with col2:
                # Add a checkbox for each movie
                if movie.get("yts_details"):
                    checkbox_key = f"download_{imdb_id}"
                    if st.checkbox("Download", key=checkbox_key):
                        selected_movies.append(movie)
                else:
                    st.write("Movie not available to download.")

        # Add a submit button for the form
        submit_button = st.form_submit_button("Download Selected Movies")

        # Handle form submission
        if submit_button:
            if selected_movies:
                for selected_movie in selected_movies:
                    try:
                        # Download the torrent for each selected movie
                        download_torrent(selected_movie)
                        st.success(f"Downloading: {selected_movie['title']} ({selected_movie['year']})")
                    except Exception as e:
                        st.error(f"Failed to download {selected_movie['title']}: {e}")
            else:
                st.warning("No movies selected for download.")

def get_yts_movie_details(imdb_id: str, with_images: bool = False, with_cast: bool = False) -> dict:
    """
    Call the YTS movie details API with the specified IMDb ID.
    """
    base_url = "https://yts.mx/api/v2/movie_details.json"
    params = {
        "imdb_id": imdb_id,
        "with_images": "true" if with_images else "false",
        "with_cast": "true" if with_cast else "false"
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    try:
        response_json = response.json()
    except ValueError:
        raise Exception("Failed to parse JSON response from API.")
    if "data" not in response_json or "movie" not in response_json["data"]:
        raise Exception("Unexpected response format from API.")
    if response_json["data"]["movie"]["id"] == 0:
        return None
    return response_json["data"]["movie"]

def choose_best_torrent(torrents):
    """
    Choose the torrent with the highest resolution quality (excluding '3D').
    """
    eligible = [t for t in torrents if t.get("quality", "").upper() != "3D"]
    if not eligible:
        return None
    def quality_rank(entry):
        qual = entry.get("quality", "")
        if qual.endswith("p"):
            try:
                return int(qual.rstrip("p"))
            except ValueError:
                return 0
        return 0
    max_quality_value = max(quality_rank(entry) for entry in eligible)
    highest_quality_entries = [
        entry for entry in eligible if quality_rank(entry) == max_quality_value
    ]
    best_entry = min(highest_quality_entries, key=lambda x: x.get("size_bytes", float("inf")))
    return best_entry

def download_file(url, output_path):
    """
    Downloads the file from the given URL and saves it to output_path.
    
    Parameters:
        url (str): The URL to download.
        output_path (str): The path where the file should be saved.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

        # Open the output file in binary write mode and save data in chunks
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return True

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6+
    except Exception as err:
        print(f"Other error occurred: {err}")

def download_torrent(movie):
    """
    Download torrent file to the designated TORRENT_FILES_DIR.
    """
    # Ensure the target directory exists.
    if not os.path.exists(TORRENT_FILES_DIR):
        os.makedirs(TORRENT_FILES_DIR, exist_ok=True)

    torrent = choose_best_torrent(movie["yts_details"]["torrents"])

    # Using os.path.join to create the output path
    output_filename = f"{movie['title']} ({movie['year']}).torrent"
    output_path = os.path.join(TORRENT_FILES_DIR, output_filename)
    
    file_downloaded = download_file(torrent["url"], output_path)
    
    if not file_downloaded:
        st.error(f"Failed to download torrent for {movie['title']}.")
        return
    else:
        qb = Client('http://127.0.0.1:8090/')
        with open(output_path, "rb") as torrent_file:
            qb.download_from_file(torrent_file)
        return
    
    
    
    



# ====================
# Streamlit UI Section
# ====================

st.title("Movie Downloader to Plex")

st.write(
    """
    This app allows you to search for movies and download them to your Plex server.
    """
)

# Add a search box
search_query = st.text_input("Search for a movie:", placeholder="Enter movie title...")
movies = []

with st.spinner("Searching..."):
    if search_query:
        movies = search_imdb(search_query)
    if movies:
        diplay_search_results(movies)


#qbit_download()

