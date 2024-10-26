import requests

from shortGPT.config.api_db import ApiKeyManager
from app.logger import logger

def search_videos(query_string, orientation_landscape=True):
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": ApiKeyManager.get_api_key("PEXELS")
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    # print(response.headers['X-Ratelimit-Limit'])
    # print(response.headers['X-Ratelimit-Remaining'])
    # print(response.headers['X-Ratelimit-Reset'])

    return json_data


def getBestVideo(query_string, orientation_landscape=True, used_vids=[]):
    vids = search_videos(query_string, orientation_landscape)
    videos = vids['videos']  # Extract the videos list from JSON

    # Filter and extract videos with width and height as 1920x1080 for landscape or 1080x1920 for portrait
    if orientation_landscape:
        filtered_videos = [video for video in videos if video['width'] >= 1920 and video['height'] >= 1080 and video['width']/video['height'] == 16/9]
    else:
        filtered_videos = [video for video in videos if video['width'] >= 1080 and video['height'] >= 1920 and video['height']/video['width'] == 16/9]

    # Sort the filtered videos by duration in ascending order
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15-int(x['duration'])))

    # Extract the top 3 videos' URLs
    for video in sorted_videos:
        for video_file in video['video_files']:
            if orientation_landscape:
                if video_file['width'] == 1920 and video_file['height'] == 1080:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
            else:
                if video_file['width'] == 1080 and video_file['height'] == 1920:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
    print("NO LINKS found for this round of search with query :", query_string)
    return None

def search_audio_on_pexels(search_term):
    """
    Search for audio on Pexels based on the given search term.
    
    Args:
        search_term (str): The search term to find audio.
        
    Returns:
        list or None: A list of audio URLs or None if no audio is found or an error occurs.
    """
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": ApiKeyManager.get_api_key("PEXELS")
    }
    
    params = {
        "query": search_term,
        "per_page": 10,
        "page": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        audio_results = response.json()
        if 'videos' in audio_results:
            audio_urls = [video['url'] for video in audio_results['videos']]  # Extract URLs
            logger.info(f"Found audio URLs: {audio_urls}")
            return audio_urls
        else:
            logger.warning("No audio found for the given search term.")
            return None  # No audio found
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")
    
    return None  # Return None in case of an error