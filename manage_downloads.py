import pandas as pd
import streamlit as st
import time
from qbittorrent import Client # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html

    
# Function to apply conditional styles
def highlight_complete(val):
    # Normalize the text to lowercase for comparison (optional)
    text = str(val).lower()
    if text == "complete":
        return "background-color: lightgreen; font-weight: bold;"
    elif text == "incomplete":
        return "background-color: lightcoral; font-weight: bold;"
    else:
        return ""

# Convert ETA: if ETA == 8640000, display as null (or empty string), if >= 3600, display hours, else minutes.
def format_eta(eta_seconds):
    if eta_seconds == 8640000:
        return None  # or you can return "" to display as an empty cell
    elif eta_seconds >= 3600:
        return f"{eta_seconds / 3600:.2f} hrs"
    else:
        return f"{eta_seconds / 60:.2f} min"

st.title("Download Manager")

qb = Client('http://127.0.0.1:8090/')

filter_options = {
    "all": "All",
    "downloading": "Downloading",
    "seeding": "Seeding",
    "completed": "Completed",
    "paused": "Paused",
    "active": "Active",
    "inactive": "Inactive",
    "resumed": "Resumed",
    "stalled": "Stalled",
    "stalled_uploading": "Stalled Uploading",
    "stalled_downloading": "Stalled Downloading",
    "errored": "Errored"
}

# A mapping dictionary with shorter, explicit state descriptions
state_mapping = {
    "error": "Error",
    "missingFiles": "Missing Files",
    "uploading": "Uploading",
    "pausedUP": "Paused (Complete)",
    "queuedUP": "Queued Upload",
    "stalledUP": "Stalled Upload",
    "checkingUP": "Checked (Complete)",
    "forcedUP": "Forced Upload",
    "stoppedUP": "Stopped",
    "stoppedDL": "Stopped",
    "allocating": "Allocating",
    "downloading": "Downloading",
    "metaDL": "Fetching Meta",
    "pausedDL": "Paused (Downloading)",
    "queuedDL": "Queued Download",
    "stalledDL": "Stalled Download",
    "checkingDL": "Checked (Downloading)",
    "forcedDL": "Forced Download",
    "checkingResumeData": "Chk Resume Data",
    "moving": "Moving",
    "unknown": "Unknown"
}

filter = st.selectbox("Select a torrent filter", list(filter_options.keys()), format_func=lambda x: filter_options[x], index=1, key="torrent_filter")

torrents = qb.torrents(filter=filter)  # Get torrents based on the selected filter

# Convert the torrents to a DataFrame for better display
torrents_df = pd.DataFrame(torrents)

# if df is not empty, process it
if torrents_df.empty:
    st.warning("No torrents found.")
    st.stop()

else:
    torrents_df["state"] = torrents_df["state"].map(state_mapping)
    torrents_df["complete"] = torrents_df["amount_left"].apply(lambda x: "Complete" if x == 0 else "Incomplete")
    # Convert total_size from bytes to GB (float)
    torrents_df["total_size"] = torrents_df["total_size"] / (1024**3)

    # Convert speeds from bytes/s to MB/s
    torrents_df["dlspeed"] = torrents_df["dlspeed"] / (1024**2)
    torrents_df["upspeed"] = torrents_df["upspeed"] / (1024**2)

    # Make column progress with only 3 decimal places
    torrents_df["progress"] = torrents_df["progress"].round(3)

    torrents_df["eta"] = torrents_df["eta"].apply(format_eta)

    # Replace all zeros in the DataFrame with pd.NA (null)
    torrents_df = torrents_df.replace(0, pd.NA)

    # Apply the styling function to the 'complete' column
    styled_df = torrents_df.style.map(highlight_complete, subset=["complete"])


    st.dataframe(
        styled_df,
        column_config={
            "name": st.column_config.TextColumn(
                "Name",
                help="Name of the torrent"
            ),
            "progress": st.column_config.ProgressColumn(
                "Progress",
                format="percent",
                help="Download progress percentage"
            ),
            "complete": st.column_config.SelectboxColumn(
                "Complete",
                options=["Complete", "Incomplete"],
                help="Download status"
            ),
            "state": "Status",
            "total_size": st.column_config.NumberColumn(
                "Total Size (GB)",
                format="%.2f",
                help="Total size in gigabytes"
            ),
            "dlspeed": st.column_config.NumberColumn(
                "Download Speed (MB/s)",
                format="%.2f",
                help="Download speed in MB/s"
            ),
            "upspeed": st.column_config.NumberColumn(
                "Upload Speed (MB/s)",
                format="%.2f",
                help="Upload speed in MB/s"
            ),
            # Use a text column for ETA since we are formatting it as a string.
            "eta": st.column_config.TextColumn(
                "ETA",
                help="ETA: shows in hours if ≥ 1 hour, in minutes if less. 8640000 is displayed as null."
            ),
        },
        column_order=["complete", "name", "progress", "state",
                    "total_size", "dlspeed", "upspeed", "eta"],
        hide_index=True,
        use_container_width=True
    )

    time.sleep(0.1)  # Wait for 1 second before updating again
    st.rerun()

# for torrent in torrents:
#     with st.expander(f"Torrent: {torrent['name']}", expanded=True):
#         #torrent
#         # Display torrent information
#         if torrent['amount_left'] > 0:  # If the torrent is not fully downloaded
#             progress_bar = st.progress(0)  # Initialize progress bar
#         if torrent['amount_left'] > 0 and torrent["dlspeed"]==0:
#             st.warning("Download Stopped")
#         while torrent['amount_left'] > 0 and torrent["dlspeed"]>0:  # While the torrent is not fully downloaded
#             torrents = qb.torrents(filter=filter)
#             for current_torrent in torrents:
#                 if current_torrent['hash'] == torrent['hash']:
#                     progress = current_torrent['progress']  # Update progress
#                     torrent = current_torrent
#                     break
#             if torrent['amount_left'] > 0 and torrent["dlspeed"]==0:
#                 st.warning("Download Stopped")
#                 break
#             #progress = torrent['total_downloaded'] / torrent['total_size']  # Calculate progress
#             speed_mbps = torrent['dlspeed'] / (1024)  # Convert speed to MB/s
#             if torrent['eta'] < 3600:  # If ETA is less than one hour, show in minutes
#                 eta_text = f"{round(torrent['eta'] / 60, 2)} minutes"
#             else:
#                 eta_text = f"{round(torrent['eta'] / 3600, 2)} hours"
#             progress_text = f"Downloading {round(progress * 100, 2)}%, ETA: {eta_text}, Speed: {round(speed_mbps, 2)} MB/s"
#             progress_bar.progress(progress, text=progress_text)  # Update progress bar
#             #st.write(f"Downloading {torrent['name']}: {int(progress * 100)}%")
#             time.sleep(0.1)  # Wait for 1 second before updating again

#         if torrent['amount_left'] == 0:
#             st.success(f"Download complete!")