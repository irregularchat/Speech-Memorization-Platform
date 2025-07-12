# Speech Memorization Platform

An interactive application designed to help users memorize and practice military creeds and long speeches. The app listens to your speech in real-time, transcribes it, and compares it against the original text, highlighting any discrepancies.

Imagine how lyrics from your favorite songs display on Apple Music or on karaoke apps. Now imagine using that same app to memorize and practice your speeches by gradually increasing the difficulty and removing the displayed words of the text you need to memorize.

**✅ CURRENTLY FUNCTIONAL** - Core features implemented and ready for testing! See installation instructions below.



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

### 🚧 **Planned Features**
- **Section-wise Practice**: Practice specific paragraphs or sentences
- **Stop Words Filtering**: Intelligent filtering of articles and conjunctions
- **Structured Text Format**: Rich metadata with titles, descriptions, and tags
- **Community Sharing**: Share and discover texts from other users



## Installation

### Prerequisites

- Python 3.x
- Microphone access on your device

### Steps

1. **Clone the repository**
   Don't clone if you're contributing - fork it instead. More information [here](CONTRIBUTING.md).

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

3. **Run the application**

   ```bash
   python manage.py runserver
   ```
   
   The app will open in your browser at `http://localhost:8000`

4. **Allow microphone access** when prompted by your browser

### Quick Start
1. **Login**: Use `admin` / `admin123` for demo access
2. **Select a text**: Choose from available texts or upload your own
3. **Adjust settings**: Use the mastery level slider to control word difficulty
4. **Practice**: Click "📝 Record and Transcribe" to start practicing
5. **Track progress**: View detailed analytics and performance trends


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

Roadmap

Check out the [ROADMAP.md](ROADMAP.md) file for information on project goals and milestones. This includes our file structure, navigation, and the overall structure of the project.

Collaboration Guidelines

Please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed instructions on contributing, such as setting up your environment, forking the repository, creating branches, and submitting pull requests.

License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

