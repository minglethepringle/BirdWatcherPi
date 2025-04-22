import requests
import threading
import queue
import time
import config

# Create a queue to store video file paths
video_queue = queue.Queue()

# Flag to signal the upload thread to stop
stop_upload_thread = False


def process_video(video_file_path):
    if config.DEBUG_MODE:
        print("Debug mode is enabled, skipping upload.")
        return

    # Add the video file path to the queue
    video_queue.put(video_file_path)
    print(f"Video added to upload queue: {video_file_path}")


def upload_worker():
    global stop_upload_thread

    while not stop_upload_thread or not video_queue.empty():
        # Wait for 1 min to prevent rate limiting
        time.sleep(60)

        try:
            # Get a video file path from the queue
            video_file_path = video_queue.get(timeout=1)

            print(f"Uploading video: {video_file_path}")
            upload_video(video_file_path)
        except queue.Empty:
            continue


def upload_video(video_file_path):
    print("Uploading video...")

    # Open and upload the video
    with open(video_file_path, "rb") as video_file:
        response = requests.post(
            config.STREAMABLE_API_URL,
            auth=(config.STREAMABLE_USERNAME, config.STREAMABLE_PASSWORD),
            files={"file": video_file},
        )

    # Check response
    if response.status_code == 200:
        video_info = response.json()
        short_link = f"https://streamable.com/{video_info['shortcode']}"

        print("Video uploaded successfully!")
        print(f"Video link: {short_link}")

        send_email(short_link)
    else:
        print(f"❌ Upload failed! Error: {response.text}")


def send_email(short_link):
    requests.post(
        config.MAILGUN_API_URL,
        auth=("api", config.MAILGUN_API_KEY),
        data={
            "from": f"Mailgun Sandbox <{config.MAILGUN_EMAIL}>",
            "to": f"Bird Watcher <{config.RECIPIENT_ADDRESS}>",
            "subject": "🐦 BirdWatcherPi got you new bird footage!",
            "text": f"Video link: {short_link}",
        },
    )

    print("Email sent successfully!")


# Start the upload worker thread
upload_thread = threading.Thread(target=upload_worker, daemon=True)
upload_thread.start()
