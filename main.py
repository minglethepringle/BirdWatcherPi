import config
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FfmpegOutput
from libcamera import controls
import cv2
import time
import os
import numpy as np
from enum import Enum
from video import process_video, stop_upload_thread


# Enum for tracking bird detection state
class BirdState(Enum):
    NO_BIRD = "No bird"
    SOMETHING_PRESENT = "Something present"
    BIRD_CONFIRMED = "Bird confirmed"
    POSSIBLY_LEFT = "Possibly left"


# Open the camera
camera = Picamera2()

# Set resolution (capture image in full resolution, no digital zooming) and controls
camera.configure(
    camera.create_video_configuration(
        raw={"size": (2304, 1296)},
        main={"format": "BGR888", "size": (2304, 1296), "preserve_ar": True},
        lores={"format": "BGR888", "size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT), "preserve_ar": True},
        encode="lores",
    )
)
camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": config.LENS_POSITION})
encoder = H264Encoder(framerate=config.FPS)

# Initialize the MOG2 background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False, varThreshold=200)

# Define the dimensions of the center box (ROI)
roi_width = int(config.CAMERA_WIDTH * config.ROI_SIZE)
roi_height = int(config.CAMERA_HEIGHT * config.ROI_SIZE)
roi_x = (config.CAMERA_WIDTH - roi_width) // 2
roi_y = (config.CAMERA_HEIGHT - roi_height) // 2

# Video writing
video_filename = None

# Tracking state
bird_state = BirdState.NO_BIRD
start_time = None
end_time = None
recording = False

force_quit = False


def start_recording():
    global recording, video_filename

    recording = True
    print("Recording started!")
    video_filename = os.path.join(
        config.VIDEO_SAVE_ROOT,
        time.strftime("%Y-%m-%d"),
        time.strftime("%H%M%S") + ".mp4",
    )
    # Ensure directories exist
    os.makedirs(os.path.dirname(video_filename), exist_ok=True)

    output = FfmpegOutput(video_filename, audio=config.RECORD_AUDIO, audio_sync=config.AUDIO_SYNC)
    camera.start_encoder(encoder, output, quality=Quality.HIGH)


def stop_recording():
    global recording

    recording = False
    print("Recording stopped!")

    camera.stop_encoder()

    process_video(video_filename)


def get_original_frame():
    # Capture frame from camera and downsize for processing
    original_frame = cv2.cvtColor(camera.capture_array("lores"), cv2.COLOR_RGB2BGR)

    return original_frame


def ignore_outside_roi(frame):
    # Create a mask for the center region (ROI)
    roi_mask = np.zeros_like(frame)  # Initialize the mask with zeros (black)
    roi_mask[roi_y : roi_y + roi_height, roi_x : roi_x + roi_width] = 255  # Set the ROI region to white

    # Apply the mask to the frame: mask out everything outside the ROI
    frame = cv2.bitwise_and(frame, roi_mask)

    return frame


def find_changes(frame):
    # Convert current frame to grayscale
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    frame = cv2.GaussianBlur(frame, config.GAUSSIAN_BLUR_SIZE, 0)

    # Apply the background subtractor
    frame = fgbg.apply(frame)

    # Threshold = make either full black or full white; pixel intensity >= threshold, make 255 (white)
    _, frame = cv2.threshold(frame, config.THRESHOLD_VALUE, 255, cv2.THRESH_BINARY)

    # Dilate to reinforce detected objects
    frame = cv2.dilate(frame, None, iterations=config.DILATION_ITERATIONS)

    return frame


def detect_birds(processed_frame, original_frame):
    global bird_state, start_time, end_time

    # Find moving objects
    contours, _ = cv2.findContours(processed_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    object_present = False
    for contour in contours:
        if cv2.contourArea(contour) < config.CONTOUR_AREA_THRESHOLD:  # Ignore small movements
            continue
        object_present = True  # If we detect a large enough object
        (x, y, w, h) = cv2.boundingRect(contour)
        if config.DEBUG_MODE:
            cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # State transitions
    if object_present:
        if bird_state == BirdState.NO_BIRD:
            # Something detected, let's start timer
            print("Motion detected! Waiting for confirmation...")
            bird_state = BirdState.SOMETHING_PRESENT
            start_time = time.time()
        elif bird_state == BirdState.SOMETHING_PRESENT:
            # Has it been enough time since detection?
            if time.time() - start_time >= config.MIN_DETECTION_TIME:
                print("Bird confirmed! Starting recording...")
                bird_state = BirdState.BIRD_CONFIRMED
                start_recording()
        # Object present + confirmed bird = do nothing
        elif bird_state == BirdState.POSSIBLY_LEFT:
            # In this state, that means it's been less than the detection time
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
            # Has it been enough time since left?
            if time.time() - end_time >= config.MIN_DETECTION_TIME:
                print("Bird left! Stopping recording...")
                bird_state = BirdState.NO_BIRD
                stop_recording()

    if config.DEBUG_MODE:
        # Draw ROI rectangle
        cv2.rectangle(
            original_frame,
            (roi_x, roi_y),
            ((roi_x + roi_width), (roi_y + roi_height)),
            (255, 0, 0),
            2,
        )
        cv2.putText(
            original_frame,
            str(bird_state),
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )


def run():
    global recording, force_quit, stop_upload_thread

    run_time = time.time()

    while True:
        # Check if the current time has reached or passed END_HOUR
        if not config.DEBUG_MODE and time.localtime().tm_hour >= config.END_HOUR:
            print("Reached END_HOUR during processing. Exiting run loop.")
            break

        original_frame = get_original_frame()

        processed_frame = ignore_outside_roi(original_frame)

        processed_frame = find_changes(processed_frame)

        # Give a couple seconds to allow the MOG2 background subtractor to calibrate
        if time.time() - run_time <= config.WARMUP_TIME:
            continue

        detect_birds(processed_frame, original_frame)

        if config.DEBUG_MODE:
            cv2.imshow("Original Frame", original_frame)
            cv2.imshow("Processed", processed_frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Quitting!")
            force_quit = True
            stop_upload_thread = True
            break


def main():
    while True:
        # Wait for START_HOUR
        if not config.DEBUG_MODE and (
            time.localtime().tm_hour < config.START_HOUR or time.localtime().tm_hour >= config.END_HOUR
        ):
            print("Waiting for startup time...")
            time.sleep(60)
            continue

        camera.start()
        # Run the main processing loop
        run()

        # Cleanup after exiting the run loop
        cv2.destroyAllWindows()
        if recording:
            stop_recording()
        camera.stop()

        if force_quit:
            break


if __name__ == "__main__":
    main()
