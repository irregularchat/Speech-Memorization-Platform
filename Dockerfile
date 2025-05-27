# ./Dockerfile
# Use the official Python image as the base image
FROM python:3.12-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (if necessary)
# These are common dependencies needed by packages like cryptography, pandas, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc libssl-dev libffi-dev \
    libxml2-dev libxslt1-dev zlib1g-dev \
    portaudio19-dev python3-pyaudio \
    tk-dev python3-tk \
    xvfb x11-utils \
    alsa-utils pulseaudio pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*
    
# Create a directory for PulseAudio configuration
RUN mkdir -p /etc/pulse

# Create a default client.conf file
RUN echo "default-server = unix:/tmp/pulseaudio.socket\nenable-shm = false\ndaemon-binary = /bin/true" > /etc/pulse/client.conf

# Copy the requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --upgrade pip
# Install the Python dependencies from requirements.txt
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port Streamlit will run on (optional)
EXPOSE 8880

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Use the entrypoint script to handle audio setup and start Streamlit
ENTRYPOINT ["/app/docker-entrypoint.sh"]