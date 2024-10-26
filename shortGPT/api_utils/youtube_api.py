import requests
from shortGPT.config.api_db import ApiKeyManager
from app.logger import logger

def search_youtube_videos(search_term, max_duration_minutes=5):
    """
    Search for YouTube videos based on the given search term and filter them by duration.
    
    Args:
        search_term (str): The search term to find videos.
        max_duration_minutes (int): The maximum duration of videos to return, in minutes.
        
    Returns:
        list or None: A list of dictionaries containing video titles and URLs for videos shorter than 
                      the specified duration, or None if no videos are found or an error occurs.
    """
    
    # First API call: Search for videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": search_term,
        "type": "video",
        "key": ApiKeyManager.get_api_key("YOUTUBE_API_KEY"),
        "maxResults": 10
    }
    
    try:
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        search_results = search_response.json()
        
        if 'items' in search_results and search_results['items']:
            # Extract video IDs from the search results
            video_ids = [item['id']['videoId'] for item in search_results['items']]
            
            # Second API call: Get video details including duration
            videos_url = "https://www.googleapis.com/youtube/v3/videos"
            videos_params = {
                "part": "contentDetails,snippet",
                "id": ",".join(video_ids),
                "key": ApiKeyManager.get_api_key("YOUTUBE_API_KEY")
            }
            videos_response = requests.get(videos_url, params=videos_params)
            videos_response.raise_for_status()
            videos_results = videos_response.json()
            
            # Filter videos based on duration
            filtered_videos = []
            for item in videos_results.get('items', []):
                # Convert ISO 8601 duration (PT#M#S) to total minutes
                duration = item['contentDetails']['duration']
                total_seconds = parse_iso_duration_to_seconds(duration)
                total_minutes = total_seconds / 60
                
                if total_minutes <= max_duration_minutes:
                    video_info = {
                        "title": item['snippet']['title'],
                        "url": f"https://www.youtube.com/watch?v={item['id']}"
                    }
                    filtered_videos.append(video_info)
            
            if filtered_videos:
                logger.info(f"Found YouTube videos under {max_duration_minutes} minutes: {filtered_videos}")
                return filtered_videos
            else:
                logger.warning(f"No videos found under {max_duration_minutes} minutes for the given search term.")
                return None  # No videos found matching the duration criteria
        else:
            logger.warning("No videos found for the given search term.")
            return None  # No videos found
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")
    
    return None  # Return None in case of an error

def parse_iso_duration_to_seconds(duration):
    """
    Parse ISO 8601 duration string to total seconds.
    
    Args:
        duration (str): ISO 8601 duration string (e.g., 'PT5M30S' for 5 minutes and 30 seconds).
        
    Returns:
        int: Total duration in seconds.
    """
    import re
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration)
    if not match:
        return 0
    
    hours, minutes, seconds = match.groups()
    total_seconds = (
        int(hours or 0) * 3600 +
        int(minutes or 0) * 60 +
        int(seconds or 0)
    )
    return total_seconds