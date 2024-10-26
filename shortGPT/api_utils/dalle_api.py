import requests
import json
from shortGPT.config.api_db import ApiKeyManager

def generate_simple_prompts(input_data, style='normal'):
    prompts = []
    
    for segment in input_data:
        time_range, keywords = segment
        keywords_str = ", ".join(keywords)
        
        if style != 'normal':
            prompt = f"{keywords_str} in {style} style"
        else:
            prompt = keywords_str
        
        prompts.append([time_range, prompt])
    
    return prompts

def generate_image_urls(input_data, size="1024x1792"):
    image_urls = []

    api_key = ApiKeyManager.get_api_key("OPENAI")

    api_url = "https://api.openai.com/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    for segment in input_data:
        time_range, prompt = segment
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        
        try:
            response_json = response.json()
            if "data" in response_json and response_json["data"]:
                image_url = response_json["data"][0]["url"]
                image_urls.append([time_range, image_url])
            else:
                print(f"Error in response: {response_json}")
        except Exception as e:
            print(f"Error processing request: {e}")
    
    return image_urls