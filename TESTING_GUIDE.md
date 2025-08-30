# 🎤 Speech Memorization Platform - Testing Guide

## 🚀 Application Status

✅ **Django Server Running**: http://localhost:8880  
✅ **OpenAI API Configured**: GPT-4o mini + Whisper  
✅ **AI Speech Processing**: Real-time recognition ready  
✅ **Log Monitoring**: Comprehensive logging system  

## 🌐 How to Access the Application

1. **Open your browser** and navigate to: http://localhost:8880
2. **Login** using the default credentials:
   - Username: `admin` 
   - Password: `admin123` (if superuser exists)
3. **Or create a new account** through the login page

## 🎯 Testing the AI Speech Features

### 1. **Enhanced Practice Mode**
- Go to **Texts** → Select any text → Click **"Enhanced Practice"**
- This activates the AI-powered practice interface with:
  - Real-time speech recognition via OpenAI Whisper
  - GPT-4o mini coaching and feedback
  - Adaptive word masking and hints
  - Volume level monitoring

### 2. **Microphone Test Feature**
- In Enhanced Practice mode, click **"Test Mic"** button
- Speak for 3 seconds to test audio quality
- Get AI-powered quality assessment and recommendations

### 3. **Real-Time Speech Analysis**
- Start practice session with **"Start Practice"**
- Speak the highlighted words
- Watch for:
  - Live volume indicators
  - AI transcription feedback
  - Pronunciation coaching
  - Adaptive hints when struggling

## 📊 Monitoring Logs

### Real-Time Log Monitoring
```bash
# Start comprehensive log monitoring
./monitor_logs.sh
```

### Manual Log Checking
```bash
# Django server activity
tail -f logs/django_server.log

# AI speech processing (OpenAI API calls)
tail -f logs/speech_memorization.log

# All logs together
tail -f logs/*.log
```

## 🎤 What to Look For in Logs

### Django Server Log
- HTTP requests and responses
- Authentication attempts
- CSRF protection messages
- Static file serving

### AI Speech Processing Log
- OpenAI Whisper API calls and responses
- GPT-4o mini coaching requests
- Speech analysis and confidence scores
- Audio quality assessments
- Error handling and retry attempts

## 🧪 Test Scenarios

### 1. **Basic Functionality Test**
```bash
# Run automated endpoint tests
python3 test_ai_endpoints.py
```

### 2. **Manual Browser Testing**
1. Navigate to Enhanced Practice mode
2. Click "Test Mic" - should generate AI processing logs
3. Start a practice session
4. Speak into microphone - watch for:
   - Volume bars responding
   - Transcription appearing in AI feedback panel
   - Word progression and hints
   - Coaching suggestions

### 3. **AI Integration Verification**
- Check logs for OpenAI API calls
- Verify Whisper transcription responses
- Confirm GPT-4o mini coaching messages
- Monitor error handling for API failures

## 🔧 Expected AI Log Entries

When AI features are used, you should see logs like:

```
[INFO] Processing speech input for session: abc123
[DEBUG] Whisper API request: 2.5s audio, webm format
[INFO] Transcription result: confidence=0.87, text="hello world"
[DEBUG] GPT-4o mini coaching request for word mismatch
[INFO] AI feedback generated: pronunciation tips provided
```

## 🚨 Troubleshooting

### No AI Logs Appearing?
1. Verify OpenAI API key is set: `grep OPENAI_API_KEY .env`
2. Check authentication: AI endpoints require login
3. Test with browser developer tools for JavaScript errors

### Speech Recognition Not Working?
1. Check microphone permissions in browser
2. Test with "Test Mic" feature first
3. Verify audio format support (WebM/WAV)

### Server Issues?
```bash
# Check if server is running
ps aux | grep "manage.py runserver"

# Restart if needed
python3 manage.py runserver 8880
```

## 📈 Performance Monitoring

- Monitor response times for AI API calls
- Check audio processing latency
- Observe memory usage during speech sessions
- Track error rates and retry attempts

## 🎯 Key Features to Test

1. **Speech-to-Text Accuracy**: Test with various accents and speeds
2. **Word Masking Logic**: Different mastery levels (0-100%)
3. **Adaptive Hints**: Automatic progression (letter → partial → full)
4. **AI Coaching**: Contextual feedback quality
5. **Audio Quality**: Various microphone setups
6. **Session Management**: Start, pause, resume, restart
7. **Progress Tracking**: Word-level mastery improvements

---

## 🎉 Success Indicators

✅ Real-time speech transcription working  
✅ AI coaching providing helpful feedback  
✅ Word highlighting and masking functional  
✅ Progressive hints activating automatically  
✅ Audio quality validation working  
✅ Session state persisting correctly  
✅ Logs showing detailed AI processing  

Happy testing! 🚀