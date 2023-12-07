import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
# Datetime
from datetime import datetime, timedelta
import pytz
# News API
from newsapi import NewsApiClient
# OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import re
import ast
import time
# Database
import sqlite3
# Crawler
import requests
from bs4 import BeautifulSoup
import random

# Interval of items (seconds)
interval_of_items = 30 * 60

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def setup_database():
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()
    # Modify the table to add new columns for chineseTitle and summary
    c.execute('''
        CREATE TABLE IF NOT EXISTS news
        (title TEXT PRIMARY KEY,
        content TEXT,
        source_name TEXT,
        url TEXT,
        publishedAt TEXT, 
        chineseTitle TEXT,
        summary TEXT,
        newsPageContent TEXT,
        newsComment TEXT)
    ''')
    conn.commit()
    conn.close()


# Checking the existence of news in the database
def check_existence(news_title):
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()

    c.execute("SELECT title FROM news WHERE title=?", (news_title,))
    data = c.fetchone()

    conn.close()

    if data is None:
        return False
    else:
        return True


# Inserting new news into the database
def insert_news(news_data):
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()

    # Check if chineseTitle and summary keys exist in news_data
    chinese_title = news_data.get('chineseTitle', '')
    summary = news_data.get('summary', '')
    news_page_content = news_data.get('newsPageContent', '')
    news_comment = news_data.get('newsComment', '')

    # Update the SQL query to include the new columns
    c.execute(
        "INSERT INTO news (title, content, source_name, url, publishedAt, chineseTitle, summary, newsPageContent, newsComment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (news_data['title'], news_data['content'], news_data['source']['name'], news_data['url'], news_data['publishedAt'], chinese_title, summary, news_page_content, news_comment),
    )
    conn.commit()
    conn.close()


def update_news_chinese_info(title, news_page_content, chinese_title, summary):
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()

    # Use a parameterized SQL query to prevent SQL injection and update the fields
    c.execute(
        "UPDATE news SET newsPageContent=?, chineseTitle=?, summary=? WHERE title=?",
        (news_page_content, chinese_title, summary, title),
    )
    conn.commit()
    conn.close()


def update_news_comment(title, news_comment):
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()

    # Use a parameterized SQL query to prevent SQL injection and update the fields
    c.execute(
        "UPDATE news SET newsComment=? WHERE title=?",
        (news_comment, title),
    )
    conn.commit()
    conn.close()


# Define a few command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text("Hi! I am your channel automation bot.")


# Init News API
newsapi = NewsApiClient(api_key='YOUR_API_KEY')


async def get_top_headlines():
    # /v2/top-headlines
    top_headlines = newsapi.get_top_headlines(page_size=100)
    # Get all the news titles from the response
    list_news_titles_top_headlines = [article['title'] for article in top_headlines['articles']]
    # Convert the list of news titles to a single string
    text_news_titles_top_headlines = ''
    for index, news_title in enumerate(list_news_titles_top_headlines):
        text_news_titles_top_headlines += str(index + 1) + '. ' + news_title + '\n'
    return top_headlines, text_news_titles_top_headlines


# Init OpenAI
openai_api_key = 'YOUR_OPENAI_API_KEY'


async def get_openai_response_of_extracting_news():
    chat = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name='gpt-3.5-turbo-16k')

    #
    top_headlines, text_news_titles_top_headlines = await get_top_headlines()

    news_prompt = "You are a professional news editor and your task is to filter news headlines above and return the news numbers that meet the requirements of a specified topic. The specified topics are: Global Emergency News, Guangzhou, Shenzhen or Hong Kong Local Information, AI and Technology Frontier, Finance and Economy. Your return result can only contain news numbers that meet the requirements of the specified topic in list-like format (e.g. [1, 3, 5, 8]). DO NOT output the original title nor anything else."

    res = chat(
        [
            HumanMessage(content=text_news_titles_top_headlines + '\n\n' + news_prompt)
        ]
    )

    print(res.content)

    res_content = res.content

    pattern = r"\[(.+?)\]"
    lists = re.findall(pattern, res_content)
    combined_list = []

    for lst in lists:
        if lst:
            result = ast.literal_eval(lst)
            if isinstance(result, int):  # Check if the result is an integer
                combined_list.append(result)  # If it is, append to the list
            else:
                combined_list.extend(result)  # If not, extend the list

    print(combined_list)

    list_news_top_headlines = [article for article in top_headlines['articles']]
    # Extract items using list comprehension
    extracted_list = [list_news_top_headlines[i - 1] for i in combined_list]
    return extracted_list


async def convert_to_hongkong_time(timestamp_str):
    # Convert the timestamp to a datetime object
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S%z')

    # Set the original timezone to GMT
    timestamp = timestamp.replace(tzinfo=pytz.timezone('GMT'))

    # Set the Hong Kong timezone
    hong_kong_tz = pytz.timezone('Asia/Hong_Kong')
    # Convert the timestamp to Hong Kong time
    hong_kong_time = timestamp.astimezone(hong_kong_tz)

    # Format the converted time in the desired string representation
    converted_time = hong_kong_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    return converted_time

async def get_hongkong_time():
    # Get the current UTC time, with UTC timezone information
    server_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Convert server time to Hong Kong time
    hong_kong = pytz.timezone('Asia/Hong_Kong')
    hong_kong_time = server_time_utc.astimezone(hong_kong)

    # Format the time string as requested
    formatted_time = hong_kong_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    return formatted_time

async def download_news_content(url):
    try:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Avant Browser/1.2.789rel1 (http://www.avantbrowser.com)',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5',
            'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9',
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
            'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1',
            'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.120 Safari/535.2',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7',
            'Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.9pre) Gecko/2008072421 Minefield/3.0.2pre',
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78'
        ]

        # Randomly select a user-agent
        user_agent = random.choice(user_agents)

        headers = {
            'User-Agent': user_agent
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        article_text = soup.get_text()
        return article_text
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


async def summarize_news_in_chinese(news_data):
    # Download the whole page content of news_data['url']
    article_content = await download_news_content(news_data['url'])

    if article_content:
        summarization_prompt = (
                article_content + """\n\nYou are a professional news editor and your task is to summarise the articles in the news page above. The articles may be written in a language such as English, but your summary is to be done in Chinese (Simplified). Your return result should only contain the news headlines and summary content in the format below:\n<CHINESE TITLE>\n<SUMMARY>\nPlease do not output any other content."""
        )

        chat = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name='gpt-4-1106-preview')

        # Use OpenAI to read the whole page and output the summary of this page in Chinese
        res = chat(
            [
                HumanMessage(content=summarization_prompt)
            ]
        )

        # Assuming that the response successfully contains a summary in Chinese
        summary_in_chinese = res.content

        return article_content, summary_in_chinese
    else:
        return "无法下载新闻内容", "无法提供新闻摘要"  # "Unable to download the article content, so cannot provide a summary."


async def generate_news_comment(news_page_content):
    comment_prompt = (
            news_page_content + """\n\nAs a knowledgeable, educated and professional news commentator, your task is to make a short comment on the above news, analysing the implications of the news from various perspectives and then give your final views. Please note, that you need to provide substantial comments, not empty rhetoric. You should fully utilize analytical thinking, instead of using too many exaggerated adjectives to elaborate your argument. When you list the sub-points, please use the form of bullet points to present them. Give your comment in Chinese (Simplified)."""
    )

    chat = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name='gpt-4-1106-preview')

    # Use OpenAI to read the whole page and output the summary of this page in Chinese
    res = chat(
        [
            HumanMessage(content=comment_prompt)
        ]
    )

    # Assuming that the response successfully contains a summary in Chinese
    news_comment = res.content

    return news_comment


async def clean_brackets(original_string):
    if original_string.startswith("《") and original_string.endswith("》") or \
      original_string.startswith("<") and original_string.endswith(">"):
        return original_string[1:-1]
    else:
        return original_string


async def channel_automation(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for channel automation."""
    channel_id = "YOUR_CHANNEL_ID"

    # news_data = {
    #     "source": {"id": "national-geographic", "name": "National Geographic"},
    #     "author": "Emily Sohn",
    #     "title": "Can ending inflammation help win our battle against depression? - National Geographic",
    #     "description": "Multiple lines of research suggest that inflammation in the body can affect the brain and alter mood—a finding that could lead to new solutions for hard-to-treat issues.",
    #     "url": "https://www.nationalgeographic.com/premium/article/inflammation-depression-mental-health",
    #     "urlToImage": "https://i.natgeofe.com/n/b849eb68-71c6-44cd-b69a-23f0d595d033/GettyImages-1124669149_16x9.jpg?w=1200",
    #     "publishedAt": "2023-11-01T14:09:41Z",
    #     "content": "Chronic illness can be tough on mental health. Depression affects 42 percent of cancer patients, according to the Centers for Disease Control and Prevention, as many as 42 percent of people with rhe… [+12477 chars]"
    # }

    list_news_data = await get_openai_response_of_extracting_news()

    # Get the current date (Hong Kong time)
    current_date = datetime.now(pytz.timezone('Asia/Hong_Kong'))

    # Filter the news list to include only articles not in the db
    list_news_data = [news_data for news_data in list_news_data if not check_existence(news_data['title'])]

    if not list_news_data:  # return early if no new news to post
        return

    # Calculate the number of seconds per item considering "interval_of_items" minutes
    seconds_per_item = interval_of_items / (2 * len(list_news_data))

    # Iterate through the list
    for news_data in list_news_data:

        print(news_data)

        # Insert news data into the database
        insert_news(news_data)

        # Generate summary in Chinese
        news_page_content, chinese_title_and_summary = await summarize_news_in_chinese(news_data)

        if chinese_title_and_summary == "无法提供新闻摘要" or len(chinese_title_and_summary.split('\n')) != 2:
            # Format the news message
            message = f"*{news_data['title']}*\n\n"
            message += f"{news_data['content']}\n\n"
            message += f"from _{news_data['source']['name']}_, [Source]({news_data['url']})\n"
            message += f"{await convert_to_hongkong_time(news_data['publishedAt'])}\n"
            # Send the news message
            await context.bot.send_message(channel_id, text=message, parse_mode="Markdown")
            # Sleep for a while
            time.sleep(seconds_per_item)
        else:
            news_data['chineseTitle'], news_data['summary'] = chinese_title_and_summary.split('\n')
            # Clean the string
            news_data['chineseTitle'] = await clean_brackets(news_data['chineseTitle'])
            news_data['summary'] = await clean_brackets(news_data['summary'])
            # Update the entry in the database
            update_news_chinese_info(news_data['title'], news_page_content, news_data['chineseTitle'], news_data['summary'])
            # Format the news message
            message = f"*{news_data['chineseTitle']}*\n\n"
            message += f"{news_data['summary']}\n\n"
            message += f"来源：_{news_data['source']['name']}_，[阅读原文]({news_data['url']})\n"
            message += f"{await convert_to_hongkong_time(news_data['publishedAt'])}\n"
            # Send the news message
            await context.bot.send_message(channel_id, text=message, parse_mode="Markdown")
            # Sleep for a while
            time.sleep(seconds_per_item)
            # Generate news comment
            news_comment = f"*时事速评：{news_data['chineseTitle']}*\n\n"
            content_news_comment = await generate_news_comment(news_page_content)
            # Update the entry in the database
            update_news_comment(news_data['title'], content_news_comment)
            # Format the news comment
            content_news_comment = content_news_comment.replace('**', '*')
            news_comment += content_news_comment
            news_comment += f"\n\n来源：_参考消息_\n"
            news_comment += f"{await get_hongkong_time()}\n"
            # Send news comment
            await context.bot.send_message(channel_id, text=news_comment, parse_mode="Markdown")
            # Sleep for a while
            time.sleep(seconds_per_item)


def main() -> None:
    """Run bot."""
    # Set up the SQLite database
    setup_database()

    # Create the Application and pass it your bot's token
    application = Application.builder().token("YOUR-BOT-S-TOKEN").build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))

    # Run channel automation immediately upon startup
    application.job_queue.run_once(channel_automation, when=0)

    # Schedule channel automation message every "interval_of_items" minutes (adjust the interval as desired)
    application.job_queue.run_repeating(channel_automation, interval=interval_of_items)

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()