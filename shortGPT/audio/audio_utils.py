import os
import subprocess
import requests
import time

import yt_dlp

from shortGPT.audio.audio_duration import get_asset_duration
from shortGPT.config.api_db import ApiKeyManager
from datetime import datetime
from app.logger import logger

CONST_CHARS_PER_SEC = 20.5  # Arrived to this result after whispering a ton of shorts and calculating the average number of characters per second of speech.

WHISPER_MODEL = None


def downloadYoutubeAudio(url, outputFile):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        "format": "bestaudio/best",
        "outtmpl": outputFile
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(
                url,
                download=True)
            if (not os.path.exists(outputFile)):
                raise Exception("Audio Download Failed")
            return outputFile, dictMeta['duration']
    except Exception as e:
        print("Failed downloading audio from the following video/url", e.args[0])
    return None


def speedUpAudio(tempAudioPath, outputFile, expected_duration=None):  # Speeding up the audio to make it under 60secs, otherwise the output video is not considered as a short.
    tempAudioPath, duration = get_asset_duration(tempAudioPath, False)
    if not expected_duration:
        if (duration > 57):
            subprocess.run(['ffmpeg', '-i', tempAudioPath, '-af', f'atempo={(duration/57):.5f}', outputFile])
        else:
            subprocess.run(['ffmpeg', '-i', tempAudioPath, outputFile])
    else:
        subprocess.run(['ffmpeg', '-i', tempAudioPath, '-af', f'atempo={(duration/expected_duration):.5f}', outputFile])
    if (os.path.exists(outputFile)):
        return outputFile


def ChunkForAudio(alltext, chunk_size=2500):
    alltext_list = alltext.split('.')
    chunks = []
    curr_chunk = ''
    for text in alltext_list:
        if len(curr_chunk) + len(text) <= chunk_size:
            curr_chunk += text + '.'
        else:
            chunks.append(curr_chunk)
            curr_chunk = text + '.'
    if curr_chunk:
        chunks.append(curr_chunk)
    return chunks

def audioToText(file_path, max_retries=5):
    api_key = ApiKeyManager.get_api_key("OPENAI")
    url = "https://api.openai.com/v1/audio/transcriptions"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    files = {
        "file": open(file_path, "rb"),
    }

    data = {
        "timestamp_granularities[]": "word",
        "model": "whisper-1",
        "response_format": "verbose_json",
    }

    retries = 0

    while retries < max_retries:
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()  # Raise exception for HTTP errors

            if response.status_code == 200:
                return response.json()  # Return JSON response if successful

        except requests.exceptions.RequestException as e:
            logger.error(f"Error during whisper transcription attempt {retries+1}: {e}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Retrying... ({retries}/{max_retries})")
                time.sleep(3)
            else:
                logger.error("Max retries reached. Returning null.")
                return None

    files["file"].close()
    return None  # If all retries fail, return None

def getWordsPerSec(filename):
    a = audioToText(filename)
    return len(a['text'].split()) / a['segments'][-1]['end']


def getCharactersPerSec(filename):
    a = audioToText(filename)
    return len(a['text']) / a['segments'][-1]['end']

def run_background_audio_split(sound_file_path):
    try:
        # Run spleeter command
        # Get absolute path of sound file 
        output_dir = os.path.dirname(sound_file_path)
        command = f"spleeter separate -p spleeter:2stems -o '{output_dir}' '{sound_file_path}'"

        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If spleeter runs successfully, return the path to the background music file
        if process.returncode == 0:
            return os.path.join(output_dir, sound_file_path.split("/")[-1].split(".")[0], "accompaniment.wav")
        else:
            return None
    except Exception:
        # If spleeter crashes, return None
        return None
    
def trim_silence(input_file: str, silence_threshold: str = '-15dB'):
    # Get the directory of the input file
    input_dir = os.path.dirname(input_file)
    
    # Generate output file name with current timestamp in the same directory
    timestamp = int(datetime.now().timestamp())
    output_file = os.path.join(input_dir, f"trimmed_{timestamp}.wav")
    
    # Construct the ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_file,
        '-af', f"silenceremove=1:0:{silence_threshold}",
        output_file
    ]
    
    try:
        # Run the command
        subprocess.run(command, check=True)
        logger.info(f"Successfully trimmed silence from {input_file}. Output file: {output_file}")
        return os.path.abspath(output_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error trimming silence: {e}")
        return None
