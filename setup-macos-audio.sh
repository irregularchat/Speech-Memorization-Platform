#!/bin/bash
# This script sets up audio forwarding from macOS to the Docker container

# Check if homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install it first: https://brew.sh/"
    exit 1
fi

# Install PulseAudio and socat if not already installed
echo "Checking for PulseAudio..."
if ! command -v pulseaudio &> /dev/null; then
    echo "Installing PulseAudio..."
    brew install pulseaudio
fi

echo "Checking for socat..."
if ! command -v socat &> /dev/null; then
    echo "Installing socat..."
    brew install socat
fi

# Create a PulseAudio config for macOS
PULSE_CONFIG_DIR="$HOME/.config/pulse"
mkdir -p "$PULSE_CONFIG_DIR"

echo "Creating PulseAudio configuration..."
cat > "$PULSE_CONFIG_DIR/default.pa" <<EOL
#!/usr/bin/pulseaudio -nF

# Load core protocols
load-module module-device-restore
load-module module-stream-restore
load-module module-card-restore

# Load audio drivers appropriate for Mac
load-module module-coreaudio-detect

# Make PulseAudio accessible over TCP for Docker
load-module module-native-protocol-tcp auth-anonymous=1 listen=0.0.0.0

# Set default sink and source
set-default-sink 0
set-default-source 0

# Set fallback sink and source
set-fallback-sink 0
set-fallback-source 0
EOL

echo "Creating client configuration..."
cat > "$PULSE_CONFIG_DIR/client.conf" <<EOL
default-server = localhost
EOL

# Check for existing PulseAudio process
if pgrep -x "pulseaudio" > /dev/null; then
    echo "PulseAudio is already running. Restarting it with new configuration..."
    pulseaudio --kill
    sleep 2
fi

# Start PulseAudio in daemon mode with our config
echo "Starting PulseAudio..."
pulseaudio --start --exit-idle-time=-1

# Find the IP address of the host machine (that Docker containers can reach)
HOST_IP=$(ifconfig en0 | grep 'inet ' | awk '{print $2}')
if [ -z "$HOST_IP" ]; then
    HOST_IP=$(ifconfig en1 | grep 'inet ' | awk '{print $2}')
fi

if [ -z "$HOST_IP" ]; then
    echo "Could not determine host IP address. Using localhost."
    HOST_IP="127.0.0.1"
fi

echo "Host IP: $HOST_IP"

# Update .env file with PulseAudio host
echo "Updating .env file with PULSE_SERVER=$HOST_IP"
if grep -q "PULSE_SERVER=" .env; then
    sed -i '' "s/PULSE_SERVER=.*/PULSE_SERVER=$HOST_IP/" .env
else
    echo "PULSE_SERVER=$HOST_IP" >> .env
fi

echo "Setup complete. Now you can run your Docker container with audio support."
echo "Run: docker-compose down && docker-compose build && docker-compose up"
