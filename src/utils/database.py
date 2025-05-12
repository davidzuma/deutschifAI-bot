import contextlib
import os

import pandas as pd
import sqlitecloud
from dotenv import load_dotenv
import random
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()
SQLITECLOUD_API_KEY = os.getenv("SQLITECLOUD_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@contextlib.contextmanager
def get_db_connection():
    conn = sqlitecloud.connect(
        f"sqlitecloud://ctemvrrusk.sqlite.cloud:8860?apikey={SQLITECLOUD_API_KEY}"
    )
    db_name = "vocabulary.db"
    conn.execute(f"USE DATABASE {db_name}")
    try:
        yield conn
    finally:
        conn.close()

def create_german_stories_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS german_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            difficulty_level TEXT NOT NULL,
            creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            poll_question TEXT NOT NULL,
            poll_option_a TEXT NOT NULL,
            poll_option_b TEXT NOT NULL,
            poll_option_c TEXT NOT NULL,
            correct_option TEXT NOT NULL
        )
        """
        )
        conn.commit()



def insert_german_story(title, content, difficulty_level, poll_question, poll_option_a, poll_option_b, poll_option_c, correct_option):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO german_stories 
            (title, content, difficulty_level, poll_question, poll_option_a, poll_option_b, poll_option_c, correct_option) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, content, difficulty_level, poll_question, poll_option_a, poll_option_b, poll_option_c, correct_option),
        )
        conn.commit()
        return cursor.lastrowid

def generate_german_story_data():
    # Ensure OPENAI_API_KEY is set in the environment
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7, api_key=OPENAI_API_KEY)

    # Topics from Atomic Habits
    topics = [
        "Kleine Gewohnheiten, große Veränderungen",
        "Die Macht der 1% Verbesserung",
        "Identitätsbasierte Gewohnheiten",
        "Die vier Gesetze der Verhaltensänderung",
        "Das Gesetz der Offensichtlichkeit",
        "Das Gesetz der Attraktivität",
        "Das Gesetz der Einfachheit",
        "Das Gesetz der Zufriedenheit",
        "Umgebung gestalten für Erfolg",
        "Die Zwei-Minuten-Regel",
        "Gewohnheiten verfolgen und messen",
        "Der Verbündeten-Effekt",
    ]

    difficulty_levels = ["A2", "B1"]

    story_prompt = ChatPromptTemplate.from_template(
        "Schreibe eine kurze deutsche Geschichte (150-200 Wörter) für Sprachlerner auf {difficulty_level} Niveau. "
        "Das Thema der Geschichte sollte '{topic}' sein, basierend auf dem Buch 'Atomic Habits'. "
        "Gib der Geschichte auch einen passenden Titel. "
        "Erstelle dann eine Multiple-Choice-Frage zur Geschichte mit drei Optionen (A, B, C). "
        "Gib am Ende die richtige Antwort an (A, B oder C). "
        "Formatiere die Ausgabe wie folgt:\n"
        "TITEL: [Dein Titel hier]\n"
        "GESCHICHTE: [Deine Geschichte hier]\n"
        "FRAGE: [Deine Frage hier]\n"
        "A. [Option A]\n"
        "B. [Option B]\n"
        "C. [Option C]\n"
        "RICHTIGE ANTWORT: [A, B oder C]"
    )

    topic = random.choice(topics)
    difficulty_level = random.choice(difficulty_levels)

    story_response = llm.invoke(story_prompt.format_messages(topic=topic, difficulty_level=difficulty_level)).content
    
    # Parse the response
    lines = story_response.split('\n')
    title = lines[0].split(': ', 1)[1]
    content = '\n'.join([line for line in lines[1:] if not line.startswith(('FRAGE:', 'A.', 'B.', 'C.', 'RICHTIGE ANTWORT:'))])
    question = next(line for line in lines if line.startswith('FRAGE:')).split(': ', 1)[1]
    options = [line.split('. ', 1)[1] for line in lines if line.startswith(('A.', 'B.', 'C.'))]
    correct_answer = next(line for line in lines if line.startswith('RICHTIGE ANTWORT:')).split(': ', 1)[1]
    
    return {
        'title': title.strip(),
        'content': content.strip(),
        'difficulty_level': difficulty_level,
        'poll_question': question.strip(),
        'poll_option_a': options[0].strip(),
        'poll_option_b': options[1].strip(),
        'poll_option_c': options[2].strip(),
        'correct_option': correct_answer.strip()
    }

def populate_german_stories_table(num_stories=10):
    for _ in range(num_stories):
        story_data = generate_german_story_data()
        insert_german_story(
            story_data['title'].replace('ß', 'ss'), 
            story_data['content'].replace('ß', 'ss'), 
            story_data['difficulty_level'].replace('ß', 'ss'),
            story_data['poll_question'].replace('ß', 'ss'),
            story_data['poll_option_a'].replace('ß', 'ss'),
            story_data['poll_option_b'].replace('ß', 'ss'),
            story_data['poll_option_c'].replace('ß', 'ss'),
            story_data['correct_option'].replace('ß', 'ss')
        )
    print(f"{num_stories} German stories have been added to the database.")

def get_random_german_story():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, content, difficulty_level, poll_question, poll_option_a, poll_option_b, poll_option_c, correct_option
            FROM german_stories 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
    
    if result:
        return {
            'title': result[0],
            'content': result[1],
            'difficulty_level': result[2],
            'poll_question': result[3],
            'poll_option_a': result[4],
            'poll_option_b': result[5],
            'poll_option_c': result[6],
            'correct_option': result[7]
        }
    else:
        return None

if __name__ == "__main__":
    create_german_stories_table()
    populate_german_stories_table()