# Debug
import logging
# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
# Time
from datetime import datetime
import pytz
import time
from timezone_conversion import convert_to_hongkong_time, get_hongkong_time
# News Processing
from news_processing import get_openai_response_of_extracting_news
from news_processing import summarize_news_in_chinese
from news_processing import generate_news_comment
from news_processing import clean_brackets
# Database
from sqlite_connect import setup_database, check_existence
from sqlite_insert import insert_news
from sqlite_update import update_news_chinese_info, update_news_comment
# Secrets
import os
from dotenv import load_dotenv

load_dotenv()
channel_id = os.environ.get('CHANNEL_ID')
bot_s_token = os.environ.get('BOT_S_TOKEN')

# Interval of items (seconds)
interval_of_items = 30 * 60

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Define a few command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text("Hi! I am your channel automation bot.")


async def channel_automation(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for channel automation."""

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
            update_news_chinese_info(news_data['title'], news_page_content, news_data['chineseTitle'],
                                     news_data['summary'])
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
    application = Application.builder().token(bot_s_token).build()

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
