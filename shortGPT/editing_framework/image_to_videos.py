import requests
import os
import time
import subprocess
import random

def download_image(image_url, output_path):
    """Download image from URL and save it to the output path."""
    response = requests.get(image_url)
    with open(output_path, 'wb') as f:
        f.write(response.content)
    return output_path

def create_video_with_zoom(image_path, duration, output_path, overlay_path=None):
    """Create a video with a random zoom-in or zoom-out effect using FFmpeg. Optionally add an overlay."""

    # Define the zoom effects
    zoom_in_effect = f"scale=8000:-1,zoompan=z='zoom+0.001':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * 60)}:s=1024x1792:fps=60"
    zoom_out_effect = f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * 60)}:s=1024x1792:fps=60"

    # Randomly choose between zoom-in and zoom-out effect
    chosen_effect = random.choice([zoom_in_effect, zoom_out_effect])

    # Prepare the base command
    command = [
        'ffmpeg',
        '-loop', '1',
        '-framerate', '60',
        '-i', image_path,
        '-vf', chosen_effect,
        '-t', str(duration),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_path
    ]

    # Randomly decide to add the overlay if the overlay path is provided
    if overlay_path and random.choice([True, False]):
        # Adding the overlay to the command
        command = [
            'ffmpeg',
            '-loop', '1',
            '-framerate', '60',
            '-i', image_path,
            '-i', overlay_path,
            '-filter_complex', f"[0:v] {chosen_effect}[bg]; \
                                [1:v]scale=1024x1792,format=rgba,colorchannelmixer=aa=0.3[overlay]; \
                                [bg][overlay]overlay=W-w-10:H-h-10",
            '-t', str(duration),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]

    # Run the chosen FFmpeg command
    subprocess.run(command)

def convert_images_to_videos(image_data, output_dir="output_videos", overlay_path=None):
    """Convert image URLs into separate videos with random zoom effects and optional overlay."""
    output_videos = []

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    temp_image_path = 'videos/temp_images'

    # Create temporary folder for downloaded images
    if not os.path.exists(temp_image_path):
        os.makedirs(temp_image_path)

    for idx, (time_range, image_url) in enumerate(image_data):
        start_time, end_time = time_range
        duration = end_time - start_time

        # Download image and save it locally
        temp_image_timestamp = int(time.time())
        image_path = download_image(image_url, f'{temp_image_path}/temp_image_{temp_image_timestamp}.png')

        # Set video file path
        timestamp = int(time.time())
        video_filename = f"{output_dir}/video_{timestamp}.mp4"

        # Create a video with a random zoom effect using FFmpeg and optional overlay
        create_video_with_zoom(image_path, duration, video_filename, 'assets/video/overlay.mp4')

        # Append time range and video URL to the output
        output_videos.append([time_range, video_filename])

    # Clean up the temporary images
    for img in os.listdir(temp_image_path):
        os.remove(os.path.join(temp_image_path, img))
    os.rmdir(temp_image_path)

    return output_videos