# filename: summarize_article.py

import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

def summarize_article(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    article = soup.find_all('p')
    article_text = ""

    for element in article:
        article_text += '\n' + ''.join(element.findAll(text = True))
        
    parser = PlaintextParser.from_string(article_text, Tokenizer("english"))
    summarizer = LsaSummarizer()

    summary = summarizer(parser.document, 10) 
    summary_list = [str(sentence) for sentence in summary]
    result = ' '.join(summary_list)
    return result

url = "https://pub.towardsai.net/langchain-101-part-1-building-simple-q-a-app-90d9c4e815f3"
print(summarize_article(url))