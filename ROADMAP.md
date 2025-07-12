# ROADMAP.md
## Collaboration Guidance:


Join the Matrix Room about the project [here](https://matrix.to/#/%23speech-memorization-platform:irregularchat.com).


### Team Leaders 
[Youtube Video on Forking a Repo](https://youtu.be/a_FLqX3vGR4?si=M7v23WqeLA1zMh61&t=24)

(pull request to all your name below, this serves as a way to know who is involved in the project and to give credit where it's due):
- [ ] Research Team: 
- [ ] Documentation Team: 
- [ ] AI Integration Team: 
- [ ] Frontend Team: 
  - [ ] Styling Team:
  - [ ] User Experience Team:
- [ ] Backend Docker Team:
- [ ] Deployment Team: 
- [ ] Testing Team: 

### General Collaboration Guidelines

Don't self select thinking you don't know enough about a topic to contribute. This is a small community project with no deadlines and no pressure. We are all here to learn and have fun. Use this as an opportunity to build your skills and knowledge and use GPT and [Cursor App](https://cursor.com/) to help you along the way.

For more Collaboration Guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Navigation STRUCTURE:
The following files are required to be created to prevent future fracturing of the codebase. 

- [./utils/](./utils/) # folder containing utility functions
- [./logs/](./logs/) # folder containing log files
- [./data/](./data/) # folder containing data files
  - [./data/user_data/](./data/user_data/) # folder containing user data
    - [./data/user_data/texts/](./data/user_data/texts/) # folder containing user texts
    - [./data/user_data/logs/](./data/user_data/logs/) # folder containing user logs
  - [./data/pre_texts/](./data/pre_texts/) # folder containing pre-established texts
- [./src/](./src/) # folder containing source code
- [./assets/](./assets/) # folder containing assets
  - [./assets/css/](./assets/css/) # folder containing css files
  - [./assets/js/](./assets/js/) # folder containing javascript files
  - [./assets/images/](./assets/images/) # folder containing image files
    - [./assets/images/icons/](./assets/images/icons/) # folder containing icons
    - [./assets/images/backgrounds/](./assets/images/backgrounds/) # folder containing background images
  - [./assets/audio/](./assets/audio/) # folder containing audio files
    - [./assets/audio/sounds/](./assets/audio/sounds/) # folder containing sound files for the app
  - [./assets/video/](./assets/video/) # folder containing video files
  - [./assets/fonts/](./assets/fonts/) # folder containing font files
  - [./tests/](./tests/) # folder containing test files

## File Navigation:

### Current Structure (Streamlit-based):
- [./app.py](./app.py) # main streamlit app file (TO BE MIGRATED)
- [./requirements.txt](./requirements.txt) # current dependencies (TO BE UPDATED for Django)

### Future Structure (Post-Django Migration):
- [./manage.py](./manage.py) # Django management script
- [./speech_memorization/](./speech_memorization/) # Django project root
  - [./speech_memorization/settings/](./speech_memorization/settings/) # settings module
  - [./speech_memorization/urls.py](./speech_memorization/urls.py) # main URL configuration
  - [./speech_memorization/wsgi.py](./speech_memorization/wsgi.py) # WSGI application
  - [./speech_memorization/asgi.py](./speech_memorization/asgi.py) # ASGI application for WebSockets
- [./apps/](./apps/) # Django applications
  - [./apps/core/](./apps/core/) # core functionality
  - [./apps/memorization/](./apps/memorization/) # memorization logic and models
  - [./apps/analytics/](./apps/analytics/) # analytics and reporting
  - [./apps/users/](./apps/users/) # user management
  - [./apps/api/](./apps/api/) # REST API endpoints
- [./templates/](./templates/) # Django HTML templates
- [./static/](./static/) # CSS, JavaScript, images
- [./media/](./media/) # User-uploaded files
- [./requirements/](./requirements/) # environment-specific requirements
  - [./requirements/base.txt](./requirements/base.txt) # base requirements
  - [./requirements/development.txt](./requirements/development.txt) # dev requirements
  - [./requirements/production.txt](./requirements/production.txt) # production requirements

### Docker Files
- [./docker-compose.yml](./docker-compose.yml) # docker compose file for running the app in a container and installing dependencies that will work on any system
- [./.env](./.env) # environment variables file for the app containing sensitive information such as API keys and passwords to prevent them from being hardcoded into the app or committed to the repository
- [./Dockerfile](./Dockerfile) # docker file used for applying constraints to the app 

### Testing Files
- [./tests/app_test.py](./tests/app_test.py) # test file for the app

### MISC Files
- [./assets/images/logo_REPLACEME.png](./assets/images/logo_REPLACEME.png) # logo for the app
- [./assets/images/background_REPLACEME.png](./assets/images/background_REPLACEME.png) # background image for the app
- [./assets/images/microphone_icon_REPLACEME.png](./assets/images/microphone_icon_REPLACEME.png) # icon for the app microphone button
- [./assets/images/stop_icon_REPLACEME.png](./assets/images/stop_icon_REPLACEME.png) # icon for the app stop button
- [./assets/images/play_icon_REPLACEME.png](./assets/images/play_icon_REPLACEME.png) # icon for the app play button
- [./assets/images/pause_icon_REPLACEME.png](./assets/images/pause_icon_REPLACEME.png) # icon for the app pause button
- [./assets/images/next_icon_REPLACEME.png](./assets/images/next_icon_REPLACEME.png) # icon for the app next button
- [./assets/images/previous_icon_REPLACEME.png](./assets/images/previous_icon_REPLACEME.png) # icon for the app previous button
- [./assets/images/repeat_icon_REPLACEME.png](./assets/images/repeat_icon_REPLACEME.png) # icon for the app repeat button
- [./assets/images/shuffle_icon_REPLACEME.png](./assets/images/shuffle_icon_REPLACEME.png) # icon for the app shuffle button
- [./assets/audio/background_music_REPLACEME.mp3](./assets/audio/background_music_REPLACEME.mp3) # background music for the app ? More study needed to see if this is necessary
- [./assets/audio/click_REPLACEME.mp3](./assets/audio/click_REPLACEME.mp3) # click sound for the app
- [./assets/audio/error_REPLACEME.mp3](./assets/audio/error_REPLACEME.mp3) # error sound for the app
- [./assets/audio/success_REPLACEME.mp3](./assets/audio/success_REPLACEME.mp3) # success sound for the app
- [./assets/audio/warning_REPLACEME.mp3](./assets/audio/warning_REPLACEME.mp3) # warning sound for the app

### NON Code Files:
- [./README.md](./README.md) # readme file
- [./CHANGELOG.md](./CHANGELOG.md) # changelog file for tracking changes to the app when we start using versions
- [./CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) # code of conduct file
- [./CONTRIBUTING.md](./CONTRIBUTING.md) # contributing file

## TODO Functions:

### CRITICAL: Framework Migration
- [ ] **Convert from Streamlit to Django** - PRIORITY 1

#### Phase 1: Django Foundation (Week 1-2)
- [ ] Create Django project: `django-admin startproject speech_memorization`
- [ ] Setup Django apps: `core`, `memorization`, `analytics`, `users`, `api`
- [ ] Configure Django settings for development/staging/production environments
- [ ] Setup PostgreSQL database (migrate from file-based storage)
- [ ] Create base Django models (User, Text, Session, WordProgress, Analytics)
- [ ] Setup Django admin interface with custom admin classes
- [ ] Configure static files handling (CSS/JS) and media files (audio uploads)
- [ ] Setup Django REST Framework for API endpoints

#### Phase 2: Core Feature Migration (Week 3-4)
- [ ] **Text Management Models**: 
  - [ ] Text model (title, content, description, tags, difficulty)
  - [ ] TextSection model (for paragraph/sentence practice)
  - [ ] Custom text upload and processing
- [ ] **Spaced Repetition Engine**:
  - [ ] WordProgress model (word, mastery_level, easiness_factor, interval)
  - [ ] Migrate spaced_repetition.py logic to Django services
  - [ ] Background task processing with Celery for word calculations
- [ ] **Audio Processing**:
  - [ ] AudioSession model (recording metadata, transcription results)
  - [ ] Migrate audio_handler.py to Django views with WebSocket support
  - [ ] Real-time audio streaming with Django Channels

#### Phase 3: Frontend Development (Week 5-6)
- [ ] **Modern Frontend Stack**:
  - [ ] HTML5 templates with Bootstrap 5 or Tailwind CSS
  - [ ] JavaScript for real-time features (Web Audio API, WebSockets)
  - [ ] Progressive Web App (PWA) capabilities for mobile
  - [ ] Responsive design for mobile/tablet/desktop
- [ ] **Interactive Components**:
  - [ ] Real-time text display with auto-scroll (JavaScript timers)
  - [ ] Audio recording controls with visual feedback
  - [ ] Interactive analytics dashboard with Chart.js/D3.js
  - [ ] Drag-and-drop text upload interface

#### Phase 4: User System & Analytics (Week 7-8)
- [ ] **Authentication System**:
  - [ ] Django User model extension with profiles
  - [ ] Registration, login, password reset flows
  - [ ] Social authentication (Google, GitHub) with django-allauth
  - [ ] User preferences and settings
- [ ] **Advanced Analytics**:
  - [ ] Migrate analytics.py to Django with proper database queries
  - [ ] Real-time analytics dashboard with filtering
  - [ ] Export capabilities (PDF reports, CSV data)
  - [ ] Performance trend visualizations

#### Phase 5: Production Setup (Week 9-10)
- [ ] **Deployment Configuration**:
  - [ ] Docker multi-stage builds (development/production)
  - [ ] nginx reverse proxy configuration
  - [ ] gunicorn/uvicorn ASGI server setup
  - [ ] PostgreSQL + Redis for caching and sessions
- [ ] **Performance & Security**:
  - [ ] Database query optimization and indexing
  - [ ] Redis caching for frequently accessed data
  - [ ] Security headers, CSRF protection, rate limiting
  - [ ] SSL certificate configuration
- [ ] **Testing & CI/CD**:
  - [ ] Comprehensive test suite (unit, integration, e2e)
  - [ ] GitHub Actions for automated testing and deployment
  - [ ] Environment-specific configurations (dev/staging/prod)

### App Basics (Post-Django Migration)
- [x] Display the app title and basic box where the text will be displayed 
- [x] Add buttons for the app
  - [x] Microphone button
  - [x] Pause / Play  button
  - [x] Restart button
  - [x] Select Text button
  - [x] Add Custom Text button
- [ ] Format speech text file in formatting that has the following and can be parsed by the app:
    - [ ] Title
    - [ ] Text
    - [ ] Time limit (optional)
    - [ ] Description (optional)
    - [ ] Tags (optional)
- [x] Create a sidebar for text selection
- [x] Load pre-established text from files # from data/pre_texts/
- [x] Display text similar to apple music or spotify or yt music lyrics, moving up the screen as the text is memorized 
- [x] Allow changing words per minute speed of the text memorization
- [x] Text background container created that can be highlighted or can be used to cover the text to show the space for a word to be memorized.

### Audio Processing
- [x] Capture audio input from the microphone
- [x] Transcribe the audio input to text
- [x] Compare the transcribed text with the original text

### Anki Style Delayed Recall 
- [ ] Identify stop words that are not needed to be removed like the , and , etc.
- [x] Automatically remove x amount of words from throughout the text once the user has memorized them (automatically) or manually (by the user) based on percentage of text memorized 0-100% where 0% is none memorized (all displayed) and 100% is all text memorized (zero displayed)

### Performance Statistics
- [x] Calculate performance statistics
- [x] Display the highlighted text and statistics to the user
- [x] Log the session results to a log file for progress tracking
### User Account Management (Requires Django Migration)
- [ ] Create User Account Management with OIDC
  - [ ] Create a user profile page
  - [ ] Allow custom text files to be shared between users # community
  - [ ] Create a progress tracking system for users most minutes spent memorizing, total words memorized, most used custom texts, etc. # gamification
  - [ ] Create a leaderboard for users # gamification
  - [ ] Create a community forum for users to discuss the app # forum.irregularchat.com
  - [x] Create a helpdesk for users to get support # Matrix Room 

## Django Migration Benefits:

### Why Django Over Streamlit:
- **Proper User Authentication**: Django's built-in user system vs Streamlit's session-only state
- **Database Integration**: Full ORM with migrations vs file-based storage
- **RESTful APIs**: Proper API endpoints for mobile apps and integrations
- **Real-time Features**: WebSocket support for live audio streaming
- **Scalability**: Production-ready with proper caching, load balancing
- **Customization**: Full control over HTML/CSS/JS vs Streamlit's limited components
- **Mobile Support**: Responsive design vs Streamlit's desktop-focused interface
- **Admin Interface**: Built-in content management vs manual file editing
- **Security**: CSRF protection, XSS prevention, secure headers
- **Performance**: Optimized queries and caching vs Streamlit's rerun model

### Post-Django Enhanced Features:
- [ ] **Mobile App Development** - Native iOS/Android apps using Django REST API
- [ ] **Offline Mode** - Progressive Web App with service workers
- [ ] **Real-time Collaboration** - Multiple users practicing together
- [ ] **Advanced Analytics Dashboard** - Interactive charts with drill-down capabilities
- [ ] **Content Management System** - Admin interface for managing texts and users
- [ ] **API for Third-party Integrations** - LMS, educational platforms
- [ ] **Multi-tenant Support** - Organizations can have their own instances
- [ ] **Advanced Security** - Rate limiting, 2FA, audit logs
- [ ] **Performance Optimization** - Redis caching, CDN integration
- [ ] **Internationalization** - Multi-language support with Django i18n 

## Running Questions
These questions are to be answered by research and testing before the app can be considered complete and will represent questions from the community have have been answered.

### Q: What studies have been done on memorization techniques for large amounts of text and their effectiveness?
A: Research on memorization techniques for large amounts of text highlights several effective methods. Spaced repetition and active recall, particularly through flashcard applications like Anki, have demonstrated significant benefits, especially in medical education. These methods improve long-term retention and exam performance, as shown by medical students’ extensive use of Anki, correlating with higher scores and better knowledge retention (Toth et al., 2023; Lu et al., 2021). Additionally, mnemonic techniques have proven more effective than rote memorization in various educational contexts, aiding in the retention of large amounts of information (van de Lint & Bosman, 2019).

Chunking, the practice of grouping information into smaller units, has been shown to enhance short-term memory retention, especially when applied to single-type information (Suppawittaya & Yasri, 2021). In public speaking and speech memorization, rhetorical techniques such as organization, elaboration, and visualization are frequently recommended to improve audience retention and recall (Wackers, 2021). The combination of these strategies—spaced repetition, mnemonic methods, chunking, and rhetorical techniques—has been found to be highly effective for retaining large volumes of information.

### Q: What are the best practices for designing an app that allows users to input and interact with text?
### Q: What are the largest challenges for people when memorizing large amounts of text?
### Q: Not trying to be cute, but like a teleprompter app?
A: Yes, it’s similar to a teleprompter, but it’s inspired by the Anki method for delayed recall and guided study. The app helps you focus on the areas that matter by identifying sections you’re already familiar with and highlighting the ones you’re struggling with. This way, it enhances your ability to recall information effectively while also giving you real-time feedback on your performance
