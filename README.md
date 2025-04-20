# BirdWatcherPi
<img style="width: 200px" src="https://github.com/user-attachments/assets/209d5610-f0c6-48f3-988d-00bcc6f1ee44"/>

## Materials
- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- USB 3.0 stick
- [USB microphone](https://www.amazon.com/dp/B08M37224H)

## Features
- Bird motion detection using OpenCV
- State transitions with debounce to prevent false positives
- Fully configurable with `config.py` file
- Records bird feeder action when bird presence confirmed
- Asynchronous multithreaded video write stream
- Uploads video to Streamable and sends notification emails via Mailgun

## Installation
1. `sudo apt update && sudo apt upgrade`
2. `sudo apt install python3-opencv`
3. Create a Streamable and Mailgun account
4. `cp config.py.example config.py`
5. Configure `config.py` to your heart's content
6. `python3 main.py`

## TODO
- [x] Organize uploaded files by date in folder
- [x] Have files have clear time
- [X] Hook up the RPI5 and normal camera
- [X] Auto upload to cloud
- [X] Auto start up program at 5am
- [ ] Do some recognition to detect if bird is present, not just bg subtraction
