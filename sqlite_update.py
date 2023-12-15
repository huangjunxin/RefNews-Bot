import sqlite3


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