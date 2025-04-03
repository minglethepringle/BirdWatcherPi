# BirdWatcherPi

## Features
- Bird motion detection using OpenCV
- State transitions with debounce to prevent false positives
- Fully configurable with `config.py` file
- Records bird feeder action when bird presence confirmed
- Uploads video to Streamable and sends notification emails via Mailgun

## Installation
1. `pip install opencv-python requests threading`
2. Create a Streamable and Mailgun account
3. `mv config.py.example config.py`
4. Configure `config.py` to your heart's content
5. `python3 main.py`

## TODO
- [x] Organize uploaded files by date in folder
- [x] Have files have clear time
- [ ] Hook up the RPI5 and normal camera
- [ ] Auto upload to cloud
- [ ]Auto start up program at 5am
