#!/bin/sh
# Start the Streamlit app in the background
streamlit run main.py --server.port=8505 --server.address=0.0.0.0 &

# Start ngrok to tunnel the Streamlit app
ngrok http --url major-needed-shrimp.ngrok-free.app 8505