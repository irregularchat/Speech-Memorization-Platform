#!/bin/bash
set -e

# Start PulseAudio in the background (if it's installed)
if command -v pulseaudio &> /dev/null; then
  echo "Starting PulseAudio server..."
  pulseaudio -D --verbose --exit-idle-time=-1 --system || echo "Failed to start PulseAudio"
  
  # Wait for PulseAudio to be fully started
  sleep 2
  
  # List audio devices to verify they're accessible
  echo "Checking available audio devices:"
  if command -v pacmd &> /dev/null; then
    pacmd list-sources || echo "No audio sources found via PulseAudio"
  fi
  
  if command -v arecord &> /dev/null; then
    echo "ALSA devices:"
    arecord -l || echo "No ALSA recording devices found"
  fi
fi

# Run the Streamlit app
echo "Starting Streamlit application..."
streamlit run streamlit_app.py --server.port=${PORT:-8880} --server.enableCORS=false
