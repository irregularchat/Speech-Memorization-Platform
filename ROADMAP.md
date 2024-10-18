# ROADMAP.md
## Collaboration Guidance:

### Team Leaders 
(pull request to all your name below):
- [ ] Research Team: 
- [ ] Documentation Team: 
- [ ] AI Integration Team: 
- [ ] Frontend Team: 
- [ ] Backend Docker Team:
- [ ] Deployment Team: 
- [ ] Testing Team: 

### General Collaboration Guidelines

Don't self select thinking you don't know enough about a topic to contribute. This is a small community project with no deadlines and no pressure. We are all here to learn and have fun. Use this as an opportunity to build your skills and knowledge and use GPT and [Cursor App](https://cursor.com/) to help you along the way.

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

## File Navigation:
### Python Files
- [./app.py](./app.py) # main app file
- [./requirements.txt](./requirements.txt) # requirements file for the app containing the dependencies that need to be installed to run the app. This is used by Dockerfile to install the dependencies.

### Docker Files
- [./docker-compose.yml](./docker-compose.yml) # docker compose file for running the app in a container and installing dependencies that will work on any system
- [./.env](./.env) # environment variables file for the app containing sensitive information such as API keys and passwords to prevent them from being hardcoded into the app or committed to the repository
- [./Dockerfile](./Dockerfile) # docker file used for applying constraints to the app 

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
- [ ] Display the app title and description
- [ ] Format speech text file in formatting that has:
    - [ ] Title
    - [ ] Text
    - [ ] Time limit (optional)
    - [ ] Description (optional)
    - [ ] Tags (optional)
- [ ] Load pre-established texts from files
- [ ] Load custom texts from user input text or file
- [ ] Create a sidebar for text selection
- [ ] Display the selected or entered text on the main page
- [ ] Capture audio input from the microphone
- [ ] Transcribe the audio input to text
- [ ] Compare the transcribed text with the original text
- [ ] Calculate performance statistics
- [ ] Display the highlighted text and statistics to the user
- [ ] Log the session results to a log file for progress tracking

## Running Questions:
### Q: What studies have been done on memorization techniques for large amounts of text and their effectiveness?
### Q: What are the best practices for designing an app that allows users to input and interact with text?
### Q: What are the largest challenges for people when memorizing large amounts of text?