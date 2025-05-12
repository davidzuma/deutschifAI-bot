from telegram import Update, Poll
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, PollAnswerHandler
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from datetime import datetime
import random
import os
from gtts import gTTS
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time
from utils.database import get_random_german_story


# Your existing imports and API key setups here
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7, api_key=OPENAI_API_KEY)

# Initialize Telegram bot
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Dictionary to store poll results
poll_results = {}

# Create a prompt template for generating German grammar content with a question
grammar_prompt = ChatPromptTemplate.from_template(
    "Erkläre ein Grammatikthema auf Deutsch-Niveau A2. "
    "Dann erstelle eine einfache Multiple-Choice-Frage auf Deutsch zum Grammatikthema "
    "mit drei Optionen (A, B, C). "
    "Gib am Ende die richtige Antwort an (A, B oder C). "
    "Formatiere die Ausgabe wie folgt:\n"
    "GRAMMATIK: [Deine Erklärung hier]\n"
    "FRAGE: [Deine Frage hier]\n"
    "OPTIONEN:\n"
    "A. [Option A]\n"
    "B. [Option B]\n"
    "C. [Option C]\n"
    "RICHTIGE ANTWORT: [A, B oder C]"
)

# Function to parse the response
def parse_response(response):
    parts = response.split("\n")
    data = {}
    current_key = None
    for part in parts:
        if part.startswith("GESCHICHTE:") or part.startswith("GRAMMATIK:"):
            data['content'] = part.split(":", 1)[1].strip()
        elif part.startswith("FRAGE:"):
            data['question'] = part.split(":", 1)[1].strip()
        elif part.startswith("OPTIONEN:"):
            data['options'] = []
        elif part.startswith(("A.", "B.", "C.")):
            data['options'].append(part.split(".", 1)[1].strip())
        elif part.startswith("RICHTIGE ANTWORT:"):
            data['correct_answer'] = part.split(":", 1)[1].strip()
    return data

# Function to generate audio file from text
def generate_audio(text, filename):
    tts = gTTS(text=text, lang='de')
    tts.save(filename)

# Function to generate and send a German story with a question poll and audio
async def send_german_content(context: ContextTypes.DEFAULT_TYPE):

    chat_id = TELEGRAM_CHAT_ID  # You need to store the chat_id when setting up the job

    # Get random story from database
    story_data = get_random_german_story()
    
    if story_data:
        story_message = f"Hier ist deine {story_data['difficulty_level']} Deutsche Geschichte:\n\n{story_data['title']}\n\n{story_data['content']}"
        await context.bot.send_message(chat_id=chat_id, text=story_message)
        
        # Generate and send audio
        audio_filename = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        generate_audio(story_data['content'], audio_filename)
        await context.bot.send_audio(chat_id=chat_id, audio=open(audio_filename, 'rb'))
        os.remove(audio_filename)  # Clean up the audio file
        
        # Send story poll
        story_poll = await context.bot.send_poll(
            chat_id=chat_id,
            question=story_data['poll_question'],
            options=[story_data['poll_option_a'], story_data['poll_option_b'], story_data['poll_option_c']],
            type=Poll.QUIZ,
            correct_option_id=ord(story_data['correct_option']) - ord('A'),
            explanation=f"Die richtige Antwort ist {story_data['correct_option']}"
        )
        
        poll_results[story_poll.poll.id] = {
            'correct_answer': story_data['correct_option'],
            'total_votes': 0,
            'correct_votes': 0
        }
    else:
        await context.bot.send_message(chat_id=chat_id, text="Es konnte keine Geschichte aus der Datenbank abgerufen werden.")

    # Generate and send grammar content
    grammar_response = llm.invoke(grammar_prompt.format_messages()).content
    grammar_data = parse_response(grammar_response)
    
    grammar_message = f"Hier ist dein A2 Grammatikthema:\n\n{grammar_data['content']}"
    await context.bot.send_message(chat_id=chat_id, text=grammar_message)
    
    # Send grammar poll
    grammar_poll = await context.bot.send_poll(
        chat_id=chat_id,
        question=grammar_data['question'],
        options=grammar_data['options'],
        type=Poll.QUIZ,
        correct_option_id=ord(grammar_data['correct_answer']) - ord('A'),
        explanation=f"Die richtige Antwort ist {grammar_data['correct_answer']}",
    )
    
    poll_results[grammar_poll.poll.id] = {
        'correct_answer': grammar_data['correct_answer'],
        'total_votes': 0,
        'correct_votes': 0
    }
    
    print(f"Geschichte, Audio, Grammatik und Umfragen gesendet um {datetime.now()}")

# Function to handle poll answers
async def handle_poll_answer(update: Update, context):
    answer = update.poll_answer
    poll_id = answer.poll_id
    
    if poll_id in poll_results:
        selected_option = chr(ord('A') + answer.option_ids[0])
        poll_results[poll_id]['total_votes'] += 1
        if selected_option == poll_results[poll_id]['correct_answer']:
            poll_results[poll_id]['correct_votes'] += 1
        
        total_votes = poll_results[poll_id]['total_votes']
        correct_votes = poll_results[poll_id]['correct_votes']
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"Aktuelle Umfrageergebnisse:\n"
                 f"Gesamtstimmen: {total_votes}\n"
                 f"Richtige Antworten: {correct_votes}\n"
                 f"Prozent richtig: {(correct_votes/total_votes)*100:.2f}%"
        )

async def start_daily_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_daily(send_german_content, time=time(hour=9, minute=0), chat_id=chat_id)
    await update.message.reply_text("Tägliche deutsche Inhalte wurden eingerichtet. Sie erhalten jeden Tag um 9:00 Uhr eine Geschichte und ein Grammatikthema.")
# Set up command handlers
application.add_handler(CommandHandler("start_daily", start_daily_content))
application.add_handler(CommandHandler("story", lambda update, context: send_german_content(context)))

# Set up poll answer handler
application.add_handler(PollAnswerHandler(handle_poll_answer))

# Run the bot
application.run_polling()