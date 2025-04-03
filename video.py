import requests
import threading
import config


def process_video(video_file_path):
    # Upload video in a separate thread
    upload_thread = threading.Thread(target=upload_video, args=(video_file_path,), daemon=True)
    upload_thread.start()


def upload_video(video_file_path):
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
