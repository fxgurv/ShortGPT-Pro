import json
import os
import re
import requests
from time import sleep, time
from app.logger import logger

import openai
import tiktoken
import yaml

from shortGPT.config.api_db import ApiKeyManager


def num_tokens_from_messages(texts, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        if isinstance(texts, str):
            texts = [texts]
        score = 0
        for text in texts:
            score += 4 + len(encoding.encode(text))
        return score
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
        See https://github.com/openai/openai-python/blob/main/chatml.md for information""")


def extract_biggest_json(string):
    json_regex = r"\{(?:[^{}]|(?R))*\}"
    json_objects = re.findall(json_regex, string)
    if json_objects:
        return max(json_objects, key=len)
    return None


def get_first_number(string):
    pattern = r'\b(0|[1-9]|10)\b'
    match = re.search(pattern, string)
    if match:
        return int(match.group())
    else:
        return None


def load_yaml_file(file_path: str) -> dict:
    """Reads and returns the contents of a YAML file as dictionary"""
    return yaml.safe_load(open_file(file_path))


def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    return json_data

from pathlib import Path

def load_local_yaml_prompt(file_path):
    _here = Path(__file__).parent
    _absolute_path = (_here / '..' / file_path).resolve()
    json_template = load_yaml_file(str(_absolute_path))
    return json_template['chat_prompt'], json_template['system_prompt']


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def gpt3Turbo_completion(chat_prompt="", system="You are an AI that can give the answer to anything", temp=0.7, model="gpt-3.5-turbo", max_tokens=1000, remove_nl=True, conversation=None):
    openai.api_key = ApiKeyManager.get_api_key("OPENAI")
    max_retry = 5
    retry = 0
    while True:
        try:
            if conversation:
                messages = conversation
            else:
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": chat_prompt}
                ]
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temp)
            text = response.choices[0].message.content.strip()
            if remove_nl:
                text = re.sub('\s+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            if not os.path.exists('.logs/gpt_logs'):
                os.makedirs('.logs/gpt_logs')
            with open('.logs/gpt_logs/%s' % filename, 'w', encoding='utf-8') as outfile:
                outfile.write(f"System prompt: ===\n{system}\n===\n"+f"Chat prompt: ===\n{chat_prompt}\n===\n" + f'RESPONSE:\n====\n{text}\n===\n')
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                raise Exception("GPT3 error: %s" % oops)
            print('Error communicating with OpenAI:', oops)
            sleep(1)

def gpt4o_completion(chat_prompt, system_message, json_schema):
    # Check for missing parameters
    if not chat_prompt:
        logger.error("chat_prompt parameter is required.")
        raise ValueError("chat_prompt parameter is required.")
    
    if not system_message:
        logger.error("system_message parameter is required.")
        raise ValueError("system_message parameter is required.")
    
    if json_schema is None:
        logger.error("json_schema parameter is required.")
        raise ValueError("json_schema parameter is required.")

    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = ApiKeyManager.get_api_key("OPENAI")

    if not api_key:
        logger.error("OpenAI API key is missing.")
        raise ValueError("API key missing. Please set the OPENAI environment variable.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": chat_prompt}
    ]

    # Build the request body
    data = {
        "model": "gpt-4o-2024-08-06",
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": json_schema
        }
    }

    # Logging the request data
    logger.info(f"Sending request to GPT-4o with system message: {system_message} and user prompt: {chat_prompt}")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Send the POST request to OpenAI
            response = requests.post(api_url, headers=headers, json=data)

            # Check for a successful response
            if response.status_code == 200:
                logger.info("Request to GPT-4o was successful.")
                response_data = response.json()
                logger.info(f"response.json(): {response_data}")

                # Extract relevant data from the response
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content']
                    # Parse the content as JSON to get title, description, and script
                    return json.loads(content)  # Assuming content is in JSON format
                else:
                    logger.error("No choices found in the response.")
                    return None
            else:
                logger.error(f"Failed to get a valid response from GPT-4o: {response.status_code}, {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with OpenAI: {str(e)}")
            if attempt < max_retries - 1:  # Only retry if not the last attempt
                logger.info("Retrying...")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return None

    logger.error("Max retries reached. Returning None.")
    return None