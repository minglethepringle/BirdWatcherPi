import cv2
import time
import os
import numpy as np
from enum import Enum

# Enum for tracking bird detection state
class BirdState(Enum):
    NO_BIRD = "No bird"
    SOMETHING_PRESENT = "Something present"
    BIRD_CONFIRMED = "Bird confirmed"
    POSSIBLY_LEFT = "Possibly left"

DEBUG_MODE = True
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
WARMUP_TIME = 10 # Give 10 seconds to allow camera to calibrate

# Open the camera
camera = cv2.VideoCapture(0)

# Set resolution
camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

# Initialize the MOG2 background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = False)

# Define the dimensions of the center box (ROI)
roi_x, roi_y = int(CAMERA_WIDTH * 0.25), int(CAMERA_HEIGHT * 0.25)  # Center start
roi_width, roi_height = int(CAMERA_WIDTH * 0.5), int(CAMERA_HEIGHT * 0.5)  # Center box size

# Video writer (initialized later)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
video_writer = None
video_filename = None

# Tracking state
bird_state = BirdState.NO_BIRD
start_time = None
end_time = None
recording = False

def start_recording():
    global recording, video_filename, video_writer  
    
    recording = True
    print("Recording started!")
    video_filename = os.path.join("/media/mingle/R", f"bird_{int(time.time())}.mp4")
    # 10 fps video
    video_writer = cv2.VideoWriter(video_filename, fourcc, 10.0, (CAMERA_WIDTH, CAMERA_HEIGHT))

def stop_recording():
    global recording, video_filename, video_writer

    recording = False
    video_writer.release()
    print("Recording stopped!")

    # TODO: Upload video to cloud

def ignore_outside_roi(frame):
    # Create a mask for the center region (ROI)
    roi_mask = np.zeros_like(frame)  # Initialize the mask with zeros (black)
    roi_mask[roi_y:roi_y+roi_height, roi_x:roi_x+roi_width] = 255  # Set the ROI region to white

    # Apply the mask to the frame: mask out everything outside the ROI
    frame = cv2.bitwise_and(frame, roi_mask)

    return frame

def find_changes(frame):
    # Convert current frame to grayscale
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    frame = cv2.GaussianBlur(frame, (21, 21), 0)

    # Apply the background subtractor
    frame = fgbg.apply(frame)

    # Threshold = make either full black or full white; pixel intensity >= 30, make 255 (white)
    _, frame = cv2.threshold(frame, 30, 255, cv2.THRESH_BINARY)

    # Dilate to reinforce detected objects
    frame = cv2.dilate(frame, None, iterations=2)

    return frame

def detect_birds(processed_frame, original_frame):
    global bird_state, start_time, end_time

    # Find moving objects
    contours, _ = cv2.findContours(processed_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    object_present = False
    for contour in contours:
        if cv2.contourArea(contour) < 600: # Ignore small movements
            continue
        object_present = True  # If we detect a large enough object
        (x, y, w, h) = cv2.boundingRect(contour)
        if DEBUG_MODE: cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # State transitions
    if object_present:
        if bird_state == BirdState.NO_BIRD:
            # Something detected, let's start timer 
            print("Motion detected! Waiting for confirmation...")
            bird_state = BirdState.SOMETHING_PRESENT
            start_time = time.time()
        elif bird_state == BirdState.SOMETHING_PRESENT:
            # Has it been one second?
            if time.time() - start_time >= 1:
                print("Bird confirmed! Starting recording...")
                bird_state = BirdState.BIRD_CONFIRMED
                start_recording()
        # Object present + confirmed bird = do nothing
        elif bird_state == BirdState.POSSIBLY_LEFT:
            # In this state, that means it's been less than 1 second
            # and it came back, so restore it to BIRD_CONFIRMED
            print("Bird left and came back!")
            bird_state = BirdState.BIRD_CONFIRMED
    else:
        # No object present + no bird = do nothing
        if bird_state == BirdState.SOMETHING_PRESENT:
            # If the detected object left before confirmation
            print("Motion not sustained, no bird detected.")
            bird_state = BirdState.NO_BIRD
        elif bird_state == BirdState.BIRD_CONFIRMED:
            # Something left, let's start timer
            print("The bird might've left? Let's see...")
            bird_state = BirdState.POSSIBLY_LEFT
            end_time = time.time()
        elif bird_state == BirdState.POSSIBLY_LEFT:
            # Has it been one second?
            if time.time() - end_time >= 1:
                print("Bird left! Stopping recording...")
                bird_state = BirdState.NO_BIRD
                stop_recording()

    if DEBUG_MODE:
        # Draw ROI rectangle
        cv2.rectangle(original_frame, (roi_x, roi_y), ((roi_x + roi_width), (roi_y + roi_height)), (255, 0, 0), 2)
        cv2.putText(original_frame, str(bird_state), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
def run():
    global recording, video_writer

    run_time = time.time()

    while True:
        ret, original_frame = camera.read()
        if not ret:
            break

        # Give a couple seconds to allow camera to calibrate
        if time.time() - run_time <= WARMUP_TIME:
            continue 

        processed_frame = ignore_outside_roi(original_frame)

        processed_frame = find_changes(processed_frame)

        detect_birds(processed_frame, original_frame)

        if recording:
            video_writer.write(original_frame)

        if DEBUG_MODE:
            cv2.imshow("Original Frame", original_frame)
            cv2.imshow("Processed", processed_frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    camera.release()
    cv2.destroyAllWindows()
    if recording:
        video_writer.release()

run()