#!/bin/bash

# Speech Memorization Platform - Log Monitor
# This script monitors all application logs in real-time

echo "🎤 Speech Memorization Platform - Log Monitor"
echo "=============================================="
echo "Monitoring logs at: $(date)"
echo ""

# Function to display log with color coding
show_log() {
    local log_file=$1
    local label=$2
    local color=$3
    
    if [ -f "$log_file" ]; then
        echo -e "${color}=== $label ===${NC}"
        if [ -s "$log_file" ]; then
            tail -n 5 "$log_file"
        else
            echo "No entries yet"
        fi
        echo ""
    fi
}

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Show current status
echo -e "${GREEN}📊 Current Status:${NC}"
echo "Server PID: $(pgrep -f 'manage.py runserver' | tr '\n' ' ')"
echo "Server Status: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8880/ 2>/dev/null || echo 'Not responding')"
echo "OpenAI API Key: $([ -n "$OPENAI_API_KEY" ] && echo 'Configured' || echo 'Missing')"
echo ""

# Show recent logs
show_log "logs/django_server.log" "Django Server" "$GREEN"
show_log "logs/speech_memorization.log" "AI Speech Processing" "$BLUE"

# Start real-time monitoring
echo -e "${YELLOW}🔍 Starting real-time log monitoring...${NC}"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor all logs simultaneously
tail -f logs/django_server.log logs/speech_memorization.log 2>/dev/null | while IFS= read -r line; do
    timestamp=$(date '+%H:%M:%S')
    
    # Color code different types of log entries
    if [[ $line == *"ERROR"* ]] || [[ $line == *"CRITICAL"* ]]; then
        echo -e "${RED}[$timestamp] $line${NC}"
    elif [[ $line == *"WARNING"* ]] || [[ $line == *"WARN"* ]]; then
        echo -e "${YELLOW}[$timestamp] $line${NC}"
    elif [[ $line == *"speech"* ]] || [[ $line == *"whisper"* ]] || [[ $line == *"ai"* ]]; then
        echo -e "${BLUE}[$timestamp] $line${NC}"
    elif [[ $line == *"POST"* ]] || [[ $line == *"GET"* ]]; then
        echo -e "${GREEN}[$timestamp] $line${NC}"
    else
        echo -e "${NC}[$timestamp] $line${NC}"
    fi
done