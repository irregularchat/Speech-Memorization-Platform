# ROADMAP.md
## Navigation STRUCTURE:
The following files are required to be created to prevent future fracturing of the codebase. 

./utils/ # folder containing utility functions
./logs/ # folder containing log files
./data/ # folder containing data files
./data/user_data/ # folder containing user data
./data/user_data/texts/ # folder containing user texts
./data/user_data/logs/ # folder containing user logs
./data/pre_texts/ # folder containing pre-established texts
./src/ # folder containing source code
./assets/ # folder containing assets
./assets/css/ # folder containing css files
./assets/js/ # folder containing javascript files
./assets/images/ # folder containing image files
./assets/images/icons/ # folder containing icons
./assets/images/backgrounds/ # folder containing background images
./assets/audio/ # folder containing audio files
./assets/audio/sounds/ # folder containing sound files for the app
./assets/video/ # folder containing video files
./assets/fonts/ # folder containing font files

## File Navigation:
### Python Files
./app.py # main app file
./requirements.txt # requirements file for the app containing the dependencies that need to be installed to run the app this is used by Dockerfile to install the dependencies
### Docker Files
./docker-compose.yml # docker compose file for running the app in a container and installing dependencies that will work on any system
./.env # environment variables file for the app containing sensitive information such as API keys and passwords to prevent them from being hardcoded into the app or committed to the repository
./Dockerfile # docker file used for applying constraints to the app 
### MISC Files
./assets/images/logo.png # logo for the app
./assets/images/background.png # background image for the app
./assets/images/microphone_icon.png # icon for the app microphone button
./assets/images/stop_icon.png # icon for the app stop button
./assets/images/play_icon.png # icon for the app play button
./assets/images/pause_icon.png # icon for the app pause button
./assets/images/next_icon.png # icon for the app next button
./assets/images/previous_icon.png # icon for the app previous button
./assets/images/repeat_icon.png # icon for the app repeat button
./assets/images/shuffle_icon.png # icon for the app shuffle button
./assets/audio/background_music.mp3 # background music for the app ? More study needed to see if this is necessary
./assets/audio/click.mp3 # click sound for the app
./assets/audio/error.mp3 # error sound for the app
./assets/audio/success.mp3 # success sound for the app
./assets/audio/warning.mp3 # warning sound for the app

### NON Code Files:
./README.md # readme file
./CHANGELOG.md # changelog file for tracking changes to the app when we start using versions
./CODE_OF_CONDUCT.md # code of conduct file
./CONTRIBUTING.md # contributing file

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