# ./Dockerfile
# Use the official Python image as the base image
# FROM python:3.12-slim
FROM python:3.9-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (if necessary)
# These are common dependencies needed by packages like cryptography, pandas, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc libssl-dev libffi-dev libasound2-dev \
    libxml2-dev libxslt1-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
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

# Command to run the Streamlit app using a shell to handle environment variable substitution
# We default to port 8880 if the PORT env var isn't defined
CMD ["sh", "-c", "streamlit run /app.py --server.port=${PORT:-8880} --server.enableCORS=false"]