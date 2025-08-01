# Speech Memorization Platform

An interactive application designed to help users memorize and practice military creeds and long speeches. The app listens to your speech in real-time, transcribes it, and compares it against the original text, highlighting any discrepancies.

Imagine how lyrics from your favorite songs display on Apple Music or on karaoke apps. Now imagine using that same app to memorize and practice your speeches by gradually increasing the difficulty and removing the displayed words of the text you need to memorize.

**✅ DEPLOYED AND LIVE** - Successfully deployed to Google Cloud Run! See [deployment guide](DEPLOYMENT_GUIDE.md) for details.

**🌐 Live Demo**: [Speech Memorization Platform](https://speech-memorization-nesvf2duwa-uc.a.run.app)

## Quick Start

### Option 1: Try the Live Demo
Visit the deployed application: [https://speech-memorization-nesvf2duwa-uc.a.run.app](https://speech-memorization-nesvf2duwa-uc.a.run.app)

### Option 2: Deploy Your Own Instance
Follow our comprehensive [Deployment Guide](DEPLOYMENT_GUIDE.md) to deploy your own instance on Google Cloud Run.

**Quick Deploy Commands:**
```bash
# Clone and setup
git clone <repository-url>
cd Speech-Memorization-Platform

# Build and deploy (Apple Silicon Macs)
docker buildx build --platform linux/amd64 \
  -t gcr.io/YOUR-PROJECT/speech-memorization:latest \
  --push .

gcloud run deploy speech-memorization \
  --image gcr.io/YOUR-PROJECT/speech-memorization:latest \
  --region us-central1 \
  --platform managed
```

### Option 3: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Recent Updates (July 2024)

✅ **Successfully Deployed to Production**
- Deployed to Google Cloud Run with full functionality
- Resolved organization policy challenges for public access
- Fixed dependency issues (librosa, numpy, etc.)
- Implemented proper database migrations in container build
- Added comprehensive deployment documentation

🔧 **Key Fixes Applied**
- Uncommented required dependencies in `requirements.txt`
- Added architecture-specific Docker builds for Apple Silicon
- Implemented proper `.gitignore` and repository cleanup
- Created minimal Django settings for cloud deployment
- Added database migrations to Dockerfile

📚 **Documentation Added**
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment guide
- Updated [LESSONS_LEARNED.md](LESSONS_LEARNED.md) with recent insights
- Troubleshooting section for common deployment issues

## Contributing

We welcome contributions to this project. Please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines on how to contribute, including setting up SSH access, forking the repository, and submitting pull requests.

For the direction of the project, please read our [ROADMAP.md](ROADMAP.md) file.

Join the Matrix Room to discuss the project: [Matrix Room](https://matrix.to/#/%23speech-memorization-platform:irregularchat.com).

## Features

### ✅ **Currently Implemented**
- **Django Architecture**: Professional web framework with proper MVC structure
- **User Authentication**: Login/logout system with user management
- **Text Management**: Database-backed text storage with metadata and tagging
- **Spaced Repetition**: SM-2 algorithm with word-level progress tracking
- **Modern UI**: Bootstrap 5 responsive interface with real-time updates
- **Practice Interface**: Interactive practice page with mastery controls
- **Performance Analytics**: Comprehensive progress tracking with charts and trends
- **Database Models**: Full ORM with proper relationships and constraints
- **Admin Interface**: Django admin for content management
- **AJAX Endpoints**: Real-time API for dynamic interactions
- **Cloud Deployment**: Production-ready Google Cloud Run deployment

### 🚧 **Planned Features**
- **Section-wise Practice**: Practice specific paragraphs or sentences
- **Stop Words Filtering**: Intelligent filtering of articles and conjunctions
- **Structured Text Format**: Rich metadata with titles, descriptions, and tags
- **Community Sharing**: Share and discover texts from other users

## Installation

### Local Development

#### Prerequisites
- Python 3.11+
- Microphone access on your device
- OpenAI API key (for enhanced speech processing)
- Google Cloud project (for Google Speech-to-Text)

#### Steps

1. **Clone the repository**
   ```bash
   git clone git@github.com:irregularchat/Speech-Memorization-Platform.git
   cd Speech-Memorization-Platform
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: If you encounter issues with `pyaudio`, install platform-specific dependencies:
   - **macOS**: `brew install portaudio`
   - **Ubuntu/Debian**: `sudo apt-get install python3-pyaudio`
   - **Windows**: PyAudio should install automatically

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   python manage.py import_texts --military-only  # Load military creeds
   ```

5. **Run the application**
   ```bash
   python manage.py runserver
   ```
   
   The app will open in your browser at `http://localhost:8000`

### Cloud Deployment (Google Cloud Run)

**For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

#### Prerequisites
- Google Cloud account with billing enabled
- Google Cloud CLI installed and authenticated
- OpenAI API key

#### Quick Deploy
```bash
# Set your project and API key
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
export OPENAI_API_KEY=your-openai-key

# Build and deploy
docker buildx build --platform linux/amd64 \
  -t gcr.io/YOUR-PROJECT/speech-memorization:latest \
  --push .

gcloud run deploy speech-memorization \
  --image gcr.io/YOUR-PROJECT/speech-memorization:latest \
  --region us-central1 \
  --platform managed
```

#### Important Notes for Deployment
1. **Dependencies**: Ensure all dependencies in `requirements.txt` are uncommented
2. **Architecture**: Use `--platform linux/amd64` for Apple Silicon Macs
3. **Organization Policies**: If you get IAM policy errors, use Google Cloud Console to disable IAM authentication
4. **Billing**: Enable billing on your Google Cloud project before deployment

### Docker Development

For local development with Docker:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build for cloud deployment
docker build -t speech-memorization .
```

## Architecture

### Core Technologies
- **Backend**: Django 5.2 with PostgreSQL/SQLite
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Speech Processing**: Google Cloud Speech-to-Text + OpenAI Whisper
- **Deployment**: Docker + Google Cloud Run
- **Authentication**: Django's built-in auth system

### Key Features
- **Phrase-based Speech Recognition**: Natural speech flow instead of word-by-word
- **Smart Progression Logic**: Continue even with missed words (60%+ accuracy)
- **Military Creeds**: Pre-loaded Army, Navy, Air Force, Marines, Coast Guard creeds
- **Real-time Processing**: WebSocket-based speech streaming (when enabled)
- **Production Ready**: Full cloud deployment with monitoring and backups

### Quick Start
1. **Create account** or use demo credentials
2. **Select a text**: Choose from military creeds or upload your own
3. **Adjust settings**: Use mastery level to control word visibility
4. **Practice speaking**: Natural speech recognition with intelligent progression
5. **Track progress**: Detailed analytics and missed word review

## Usage

### Getting Started
1. **Select Your Text**: Choose from pre-loaded military creeds and speeches, or upload your own `.txt` file
2. **Configure Settings**: 
   - Set your **Words per Minute** (50-300) for scrolling speed
   - Adjust **Mastery Level** (0-100%) to hide memorized words
   - Choose **Recording Duration** (3-30 seconds)

### Practice Modes
- **Static Display**: Read the full text with word masking based on your mastery level
- **Auto-Scroll Mode**: Enable scrolling text that highlights words as you progress
- **Live Recording**: Practice speaking and get real-time transcription and accuracy feedback

### Understanding Your Progress
- **Word Statistics**: Track how many words you've mastered vs total words
- **Performance Analytics**: View accuracy trends, practice streaks, and improvement rates
- **Session History**: Review detailed logs of your practice sessions

### Tips for Best Results
- **Speak clearly** and at a steady pace for better transcription accuracy
- **Start with 0% mastery** to see the full text, gradually increase as you improve
- **Practice regularly** to maintain your streak and see improvement trends
- **Use shorter recording durations** (5-10 seconds) when starting out

## Troubleshooting

### Common Issues

**Docker Build Failures**
- Check Docker daemon is running
- Ensure sufficient disk space (2GB+ recommended)
- Review build logs for specific dependency issues
- For Apple Silicon Macs: use `--platform linux/amd64`

**Speech Recognition Not Working**
- Verify microphone permissions in browser
- Check Google Cloud Speech API is enabled
- Ensure OpenAI API key is valid and has credits

**Database Issues**
- Run `python manage.py migrate` to apply migrations
- Check database connection settings in `.env`
- For SQLite: ensure write permissions in project directory

**Organization Policy Errors**
- Use Google Cloud Console to disable IAM authentication manually
- Or contact your organization admin to modify domain restrictions

### Getting Help
- Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions
- Check [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for deployment insights and troubleshooting
- Review [ROADMAP.md](ROADMAP.md) for project direction
- Join our [Matrix Room](https://matrix.to/#/%23speech-memorization-platform:irregularchat.com) for community support

## Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines on:
- Setting up the development environment
- Code style and testing requirements
- Submitting pull requests
- Reporting issues

## Roadmap

Check out the [ROADMAP.md](ROADMAP.md) file for information on project goals and milestones, including file structure, navigation, and overall project architecture.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

