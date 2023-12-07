# RefNews-Bot

**RefNews-Bot 参考消息（机器人）**

RefNews-Bot serves as the operational backbone of *Reference News*, your go-to platform for accessing crucial global emergency news, the latest in AI and technology trends, and financial and investment information. Embracing advanced generative AI technology, *Reference News* gathers, refines, and broadcasts information, aiming to present news events in the most straightforward and comprehensible way. By offering an alternative to the convoluted mix of imagery, text, and video streams on social networks, *Reference News* seeks to dismantle the information silos frequently constructed by recommendation algorithms.

*参考消息*是您获取全球紧急新闻、AI 等科技动态和金融投资信息的首选平台。而 *参考消息（机器人）* 则是负责运营这一平台的机器人。*参考消息*运用先进的生成式 AI 技术采集、整理和发布信息，力求以最简明易懂的方式呈现新闻事件，避免社交网络上复杂的图文视频流，打破推荐算法形成的信息茧房。

The official instance is currently running on: [@tct_refnews](https://t.me/tct_refnews)

目前官方实例运行在：[@tct_refnews](https://t.me/tct_refnews)

## Features

- **Automated News Generation**: Leveraging OpenAI's powerful language models to summarize and comment on top headlines in Simplified Chinese.
- **Channel Automation**: Regularly scheduled Telegram posts to a channel with bot generated news content and insightful comments.
- **News Relevance**: Focus on delivering global emergency news, cutting-edge AI and technology developments, as well as financial and economic reports.
- **Database Integration**: A SQLite database stores news information, ensuring that content is not duplicated and is easily retrievable.

## Setup

1. **Database Initialization**: Run `setup_database()` to create the SQLite database for storing news articles if it doesn't already exist.
2. **NewsAPI**: The project employs NewsAPI to fetch the latest top headlines. You'll need to supply your own API key in the `newsapi` initialization.
3. **OpenAI Configuration**: Configure your OpenAI API key for content generation and summarization tasks. You'll need to have access to OpenAI's GPT models and replace the placeholder in `openai_api_key`.
4. **Environment Setup**: Make sure you have Python installed along with necessary libraries such as `requests`, `BeautifulSoup`, and others mentioned in the code.
5. **Running the Bot**: Use `main()` to initiate the bot. 

## Usage

After setting up your Python environment and obtaining the necessary API keys, you can start the bot using the command:

```bash
python refnews_bot.py
```

The bot will automatically start responding to commands and posting news updates on the designated Telegram channel based on the intervals defined in the script (default 30 minutes).

## Commands

- `/start`: Initializes the bot and can also be used to trigger additional automation actions.

## Disclaimer

This project uses data provided by third-party services like NewsAPI and OpenAI. Please adhere to their respective terms of service and use the provided data ethically and legally.

## Contributions

Contributions to RefNews-Bot are welcome! Please feel free to fork the repository, make your changes, and submit a pull request.

## License

RefNews-Bot is open-sourced under the *GPL-3.0 license*.

## Contact

For any queries or support, please open an issue on the project's GitHub repository, and we'll get back to you as soon as possible.