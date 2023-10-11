import os
import json
import requests

from bs4 import BeautifulSoup

import autogen
from autogen import config_list_from_json

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# from langchain.text_splitter import RecursiveCharacterTextSplitter


import openai

from dotenv import load_dotenv

load_dotenv()

# Get api key
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
llm_config = {"config_list": config_list}
openai.api_key = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")

# user_proxy = autogen.UserProxyAgent(
#     name="User_proxy",
#     system_message="A human admin who will provide the resources to summarize and save the summary.",
#     code_execution_config={"work_dir": "summaries"},
#     human_input_mode="ALWAYS",
# )

# writer = autogen.AssistantAgent(
#     name="Writer",
#     llm_config=llm_config,
# )


def extract_article(page_content):
    extractor = autogen.AssistantAgent(
        name="Extractor",
        llm_config=llm_config,
        system_message="An AI assistant to extract the main content from the provided webpage.",
    )

    proxy = autogen.UserProxyAgent(name="proxy", llm_config=llm_config)

    proxy.initiate_chat(
        extractor,
        message=f"""You will be given some Page Content between triple backticks. It's a result of function `soup(get_text)`. Your role is to recognize where the actual content (article, blog post, etc.) begins and ends and return it to me. I want only the article text.
        [Page Content]: ```{page_content}```""",
    )

    return proxy.last_message()["content"]


def scrape(url: str):
    # scrape website, and also will summarize the content based on objective if the content is too large
    # objective is the original objective & task that user give to the agent, url is the url of the website to be scraped

    print("Scraping website...")

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
        text = soup.get_text()
        print("CONTENTTTTTT:", text)
        article = extract_article(text)
        # if len(text) > 8000:
        #     output = summary(text)
        #     return output
        # else:
        #     return text
    else:
        print(f"HTTP request failed with status code {response.status_code}")

    summary = summarize(article)
    return summary


def summarize(content):
    llm = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo-16k")

    # define the prompt template
    prompt_template = """
    Write a detailed summary of the piece of content delimited by triple backticks.\
    Convert the summary to the markdown format.\
    Content: ```{text}```
    SUMMARY:
    """

    # format prompt template
    prompt = ChatPromptTemplate.from_template(prompt_template)
    formatted_prompt = prompt.format_messages(text=content)

    # summarize content
    summary = llm(formatted_prompt)

    return summary


# def research(query):
llm_config_researcher = {
    "functions": [
        # {
        #     "name": "search",
        #     "description": "google search for relevant information",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "query": {
        #                 "type": "string",
        #                 "description": "Google search query",
        #             }
        #         },
        #         "required": ["query"],
        #     },
        # },
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
        # {
        #     "name": "summarize",
        #     "description": "Summarize a given text content",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "content": {
        #                 "type": "string",
        #                 "description": "Text content to summarize",
        #             }
        #         },
        #         "required": ["content"],
        #     },
        # },
    ],
    "config_list": config_list,
}

# researcher = autogen.AssistantAgent(
#     name="researcher",
#     # system_message="Research about a given query, collect as many information as possible, and generate detailed research results with loads of technique details with all reference links attached; Add TERMINATE to the end of the research report;",
#     system_message="",
#     llm_config=llm_config_researcher,
# )

writer = autogen.AssistantAgent(
    name="writer",
    system_message="You are a professional researcher. You specialize at summarizing content to get the essense of the provided article or blog. You will improve your summary based on the suggestions from your admin. Use scrape function to get the content based on URL. After 2 rounds of content iteration, add TERMINATE to the end of the message",
    llm_config=llm_config_researcher,
)

# reviewer = autogen.AssistantAgent(
#     name="reviewer",
#     system_message="You are a world class hash tech blog content critic, you will review & critic the written summary and provide feedback to writer.After 2 rounds of content iteration, add TERMINATE to the end of the message",
#     llm_config={"config_list": config_list},
# )

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    code_execution_config={"work_dir": "summaries"},
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="TERMINATE",
    function_map={
        "scrape": scrape,
    },
)

user_proxy.initiate_chat(
    writer,
    message="""Summarize the article: https://towardsdatascience.com/exploring-gemba-a-new-llm-based-metric-for-translation-quality-assessment-3a3383de6d1f""",
)
# message="""Summarize the article: https://www.pinecone.io/learn/series/langchain/langchain-agents/""",
# message="""Summarize the article: https://medium.com/codingthesmartway-com-blog/mastering-langchain-agents-your-personal-journey-begins-here-e4dba27c8f56""",


# user_proxy.initiate_chat(writer, message=query)


# user_proxy = autogen.UserProxyAgent(
#     name="User_proxy",
#     human_input_mode="TERMINATE",
#     function_map={
#         # "write_content": write_content,
#         "research": research,
#     },
# )

# user_proxy.initiate_chat(
#     writing_assistant, message="write a blog about autogen multi AI agent framework"
# )


# # Define research function
# def search(query):
#     url = "https://google.serper.dev/search"

#     payload = json.dumps({"q": query})
#     headers = {
#         "X-API-KEY": SERPER_API_KEY,
#         "Content-Type": "application/json",
#     }

#     response = requests.request("POST", url, headers=headers, data=payload)

#     return response.json()


###  ---------------------  ###
# <article>
# TL;DR: We demonstrate how to use autogen for local LLM application. As an example, we will initiate an endpoint using FastChat and perform inference on ChatGLMv2-6b.

# Preparations​
# Clone FastChat​
# FastChat provides OpenAI-compatible APIs for its supported models, so you can use FastChat as a local drop-in replacement for OpenAI APIs. However, its code needs minor modification in order to function properly.

# git clone https://github.com/lm-sys/FastChat.git
# cd FastChat
# Download checkpoint​
# ChatGLM-6B is an open bilingual language model based on General Language Model (GLM) framework, with 6.2 billion parameters. ChatGLM2-6B is its second-generation version.

# Before downloading from HuggingFace Hub, you need to have Git LFS installed.

# git clone https://huggingface.co/THUDM/chatglm2-6b
# Initiate server​
# First, launch the controller

# python -m fastchat.serve.controller
# Then, launch the model worker(s)

# python -m fastchat.serve.model_worker --model-path chatglm2-6b
# Finally, launch the RESTful API server

# python -m fastchat.serve.openai_api_server --host localhost --port 8000
# Normally this will work. However, if you encounter error like this, commenting out all the lines containing finish_reason in fastchat/protocol/api_protocal.py and fastchat/protocol/openai_api_protocol.py will fix the problem. The modified code looks like:

# class CompletionResponseChoice(BaseModel):
#     index: int
#     text: str
#     logprobs: Optional[int] = None
#     # finish_reason: Optional[Literal["stop", "length"]]

# class CompletionResponseStreamChoice(BaseModel):
#     index: int
#     text: str
#     logprobs: Optional[float] = None
#     # finish_reason: Optional[Literal["stop", "length"]] = None
# Interact with model using oai.Completion​
# Now the models can be directly accessed through openai-python library as well as autogen.oai.Completion and autogen.oai.ChatCompletion.

# from autogen import oai

# # create a text completion request
# response = oai.Completion.create(
#     config_list=[
#         {
#             "model": "chatglm2-6b",
#             "api_base": "http://localhost:8000/v1",
#             "api_type": "open_ai",
#             "api_key": "NULL", # just a placeholder
#         }
#     ],
#     prompt="Hi",
# )
# print(response)

# # create a chat completion request
# response = oai.ChatCompletion.create(
#     config_list=[
#         {
#             "model": "chatglm2-6b",
#             "api_base": "http://localhost:8000/v1",
#             "api_type": "open_ai",
#             "api_key": "NULL",
#         }
#     ],
#     messages=[{"role": "user", "content": "Hi"}]
# )
# print(response)
# If you would like to switch to different models, download their checkpoints and specify model path when launching model worker(s).

# interacting with multiple local LLMs​
# If you would like to interact with multiple LLMs on your local machine, replace the model_worker step above with a multi model variant:

# python -m fastchat.serve.multi_model_worker \
#     --model-path lmsys/vicuna-7b-v1.3 \
#     --model-names vicuna-7b-v1.3 \
#     --model-path chatglm2-6b \
#     --model-names chatglm2-6b
# The inference code would be:

# from autogen import oai

# # create a chat completion request
# response = oai.ChatCompletion.create(
#     config_list=[
#         {
#             "model": "chatglm2-6b",
#             "api_base": "http://localhost:8000/v1",
#             "api_type": "open_ai",
#             "api_key": "NULL",
#         },
#         {
#             "model": "vicuna-7b-v1.3",
#             "api_base": "http://localhost:8000/v1",
#             "api_type": "open_ai",
#             "api_key": "NULL",
#         }
#     ],
#     messages=[{"role": "user", "content": "Hi"}]
# )
# print(response)
# </article>
