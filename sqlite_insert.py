import sqlite3


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