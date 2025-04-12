# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/goncalo692/Torrent_Downloader.git .

RUN pip3 install -r requirements.txt

EXPOSE 8505

HEALTHCHECK CMD curl --fail http://localhost:8505/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8505", "--server.address=0.0.0.0"]



# Use the official lightweight Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Install system dependencies.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install ngrok via Apt.
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && \
    apt-get install -y ngrok

# Add the authtoken for ngrok.
RUN ngrok config add-authtoken 2vYWnSbILAKYF0c2Sf5DCgbckf8_2StcCpLfrZn11t3nvqMrp

# Clone your repository.
RUN git clone https://github.com/goncalo692/Torrent_Downloader.git .

# Install your Python dependencies.
RUN pip3 install -r requirements.txt

# Copy the entrypoint script into the container.
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the port used by Streamlit.
EXPOSE 8505

# Healthcheck for the Streamlit app.
HEALTHCHECK CMD curl --fail http://localhost:8505/_stcore/health

# Set the custom entrypoint.
ENTRYPOINT ["/app/entrypoint.sh"]



## Ignore this part, it's just for testing

sudo docker run --network=host torrent_downloader


#ngrok http --url=major-needed-shrimp.ngrok-free.app 80

ngrok http --url major-needed-shrimp.ngrok-free.app 8080