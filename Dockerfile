# Use the official Python image as the base image
FROM python:3.9-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (including PortAudio for PyAudio)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc libssl-dev libffi-dev libasound2-dev \
    libxml2-dev libxslt1-dev zlib1g-dev portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the specific app.py file to the working directory
COPY app.py /app/app.py

# Copy all application files into the container
COPY . .
## Debug by listing to make sure /app/app.py is in the container
RUN ls -l /app
# Expose the port Streamlit will run on (optional)
EXPOSE 8880

# Command to run the Streamlit app
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8880} --server.enableCORS=false"]