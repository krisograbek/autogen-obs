import autogen
from autogen import config_list_from_json


config_list = config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
)
llm_config = {"config_list": config_list}


writer = autogen.AssistantAgent(
    name="Writer",
    system_message="""
    You are a professional content researcher.\
    You specialize at summarizing content of the provided article or blog.\
    Your summaries are detailed and well structured.\
    Add TERMINATE to the end of the message""",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="TERMINATE",
)


# Start the conversation
user_proxy.initiate_chat(
    writer,
    message="""Summarize the article: https://blog.stackademic.com/using-chatgpt-for-web-scraping-a-practical-guide-673fa2bbfac1""",
)
