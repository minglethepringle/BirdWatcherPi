#######################
### GENERAL OPTIONS ###
#######################

# Set to True for bounding boxes and current state drawn onto the video.
# Set to False for clean video without any overlays
DEBUG_MODE = True

# In pixels
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Time to allow camera to calibrate when booting up, in seconds
WARMUP_TIME = 10

# Percentage of the screen for the region of interest, where detection happens
# (0 = none, 1 = full screen)
# Any movement outside this area will be ignored
ROI_SIZE = 0.5

# Root folder where videos will be saved
# Videos will be saved into a subfolder named with the current date
# and the video will be named with the time of recording
VIDEO_SAVE_ROOT = "/path/to/root"

# Frames per second for the video
# I'm still confused as to whether this is the number of frames per second
# that the VideoWriter writes or how fast the video is played back
FPS = 10.0

#########################
### DETECTION OPTIONS ###
#########################

# Size of the Gaussian blur kernel, must be odd number
# In pixels
GAUSSIAN_BLUR_SIZE = (21, 21)

# Minimum pixel intensity for a pixel to be considered "white"
# in the threshold function. Measured in 0-255 scale
THRESHOLD_VALUE = 30

# Number of times to dilate the image, to expand contours
# and reinforce detected objects
DILATION_ITERATIONS = 2

# Minimum area of a contour (white blob) to be considered a bird
# In pixels
CONTOUR_AREA_THRESHOLD = 600

# Minimum time that a bird must be present to be considered "detected",
# or that a bird has left the frame to be considered "not detected"
# This is to avoid false positives from small movements
# In seconds
MIN_DETECTION_TIME = 1

##########################
### STREAMABLE OPTIONS ###
##########################

# Streamable API endpoint, where a POST request is sent to upload the video
STREAMABLE_API_URL = "https://api.streamable.com/upload"

# Your Streamable login credentials
# You must create a Streamable account first!
STREAMABLE_USERNAME = "ABC@gmail.com"
STREAMABLE_PASSWORD = "XYZ"

#######################
### MAILGUN OPTIONS ###
#######################

# Mailgun API endpoint, where a POST request is sent to send the email
# Sandbox environments only
MAILGUN_API_URL = "https://api.mailgun.net/v3/YOUR_SANDBOX.mailgun.org/messages"

# Your Mailgun API key
# You must create a Mailgun account first!
MAILGUN_API_KEY = "YOUR_API_KEY"

# Mailgun full email with domain
# Sandbox environments only
MAILGUN_EMAIL = "postmaster@YOUR_SANDBOX.mailgun.org"

# Where the email will be sent to
# The recipient must be verified in the Mailgun sandbox
RECIPIENT_ADDRESS = "ABC@gmail.com"
