import sqlite3


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