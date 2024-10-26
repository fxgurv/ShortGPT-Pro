import json

from shortGPT.gpt import gpt_utils
from app.logger import logger

def generate_search_term(video_script):
    """Use GPT to generate a search term based on the video script."""
    # Load the YAML prompt template
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/bg_music_search_term.yaml')
    
    # Replace the placeholder with the actual video script
    chat = chat.replace("<<CONTENT>>", video_script)
    
    search_term = ""
    attempts = 0
    max_attempts = 5
    
    while not search_term and attempts < max_attempts:
        attempts += 1
        try:
            result = gpt_utils.gpt3Turbo_completion(
                chat_prompt=chat,
                system=system,
                temp=0.7,
                max_tokens=50,
                remove_nl=True
            )
            if result:
                logger.info(f"Raw API response: {result}")
                response = json.loads(result)
                if "search_term" in response:
                    search_term = response["search_term"]
                    logger.info(f"Generated search term: {search_term}")
                else:
                    logger.warning("Response did not contain 'search_term'.")
            else:
                logger.error("Received an empty response from the API.")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response.")
        except Exception as e:
            logger.error(f"Error generating search term with GPT: {e}")
            break  # Exit if an unrecoverable error occurs
    
    return search_term if search_term else None  # Return None if search_term is still empty