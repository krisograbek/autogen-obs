import os
import json
import requests
from bs4 import BeautifulSoup

import autogen
from autogen import config_list_from_json

from dotenv import load_dotenv

load_dotenv()
# Get api key
config_list = config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4",
            "gpt-4-0613",  # required for function calling
        ],
    },
)
llm_config = {"config_list": config_list, "seed": 41, "request_timeout": 240}

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")


def scrape(url: str):
    print("Using the scrape function...")
    # Prepare the URL
    browserless_url = (
        f"https://chrome.browserless.io/content?token={BROWSERLESS_API_KEY}"
    )

    # Define the headers for the request
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }

    # Define the data to be sent in the request
    data = {"url": url}

    # Convert Python object to JSON string
    data_json = json.dumps(data)

    # Send the POST request
    response = requests.post(
        browserless_url,
        headers=headers,
        data=data_json,
    )

    # Check the response status code
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.get_text()
        # print("Article text:", content)
    else:
        print(f"HTTP request failed with status code {response.status_code}")

    return content


# function callings for the agent
llm_config_writer = {
    "functions": [
        {
            "name": "scrape",
            "description": "Scraping website content based on url",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website url to scrape",
                    }
                },
                "required": ["url"],
            },
        },
    ],
    "config_list": config_list,
}


writer = autogen.AssistantAgent(
    name="Writer",
    system_message="""
    You are a professional content researcher.\
    You specialize at summarizing content of the provided article or blog.\
    Your summaries are detailed and well structured.\
    Use scrape function to get the content based on URL.\
    Add TERMINATE to the end of the message""",
    llm_config=llm_config_writer,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="TERMINATE",
    function_map={
        "scrape": scrape,
    },
)


# Start the conversation
user_proxy.initiate_chat(
    writer,
    message="""Summarize the article and highlight key takeaways: https://blog.stackademic.com/using-chatgpt-for-web-scraping-a-practical-guide-673fa2bbfac1""",
)
