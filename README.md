# deutschifai-bot

A Telegram bot for German learners that delivers daily stories and grammar quizzes, plus a Streamlit dashboard for monitoring OpenAI API costs.

---

## 🤖 Telegram Bot

The bot sends:
- A short German story (A2/B1 level) with a comprehension poll and audio.
- A grammar explanation with a quiz.
- Both are delivered daily at a scheduled time.

### Features
- Stories and grammar questions are generated using OpenAI's GPT models.
- Stories are stored in a database and selected randomly.
- Audio is generated using Google Text-to-Speech (gTTS).
- Interactive Telegram polls for comprehension and grammar.

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/davidzuma/deutschifai-bot.git
   cd deutschifai-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   SQLITECLOUD_API_KEY=your_sqlitecloud_api_key
   ```

4. **Initialize the database**
   ```bash
   python src/utils/database.py
   ```

5. **Run the bot**
   ```bash
   python src/main.py
   ```

6. **Start daily content**
   - In Telegram, send `/start_daily` to the bot.

---

## 📊 Monitoring Dashboard

A Streamlit app to visualize your OpenAI API usage and costs.

### Features

- View total and daily costs.
- Breakdown by model.
- Raw usage data table.

### Setup & Usage

1. **Install Streamlit and other dependencies**
   ```bash
   pip install streamlit matplotlib pandas python-dotenv requests
   ```

2. **Set your OpenAI API key**  
   (Already in your `.env` file.)

3. **Run the dashboard**
   ```bash
   streamlit run monitoring/costs.py
   ```

4. **Open the dashboard**  
   Visit the local URL provided by Streamlit in your browser.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
