import os
import json
import sqlite3
import difflib
import asyncio
from colorama import Fore, Style, init as colorama_init
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "memory.db"
BACKUP_FILE = "memory_backup.json"

# === COLOR LOGGING ===
colorama_init(autoreset=True)
def log_info(msg): print(Fore.CYAN + "[INFO] " + Style.RESET_ALL + msg)
def log_success(msg): print(Fore.GREEN + "[SUCCESS] " + Style.RESET_ALL + msg)
def log_warn(msg): print(Fore.YELLOW + "[WARNING] " + Style.RESET_ALL + msg)
def log_error(msg): print(Fore.RED + "[ERROR] " + Style.RESET_ALL + msg)

# === DATABASE SETUP ===
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT
            )
        """)
    log_success("SQLite DB initialized.")

def save_memory(question: str, answer: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO memory (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
    export_to_json()
    log_success(f"Learned: '{question}' → '{answer}'")

def get_answer(user_question: str):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT question, answer FROM memory")
        rows = cur.fetchall()
        questions = [row[0] for row in rows]
        match = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.6)
        if match:
            for q, a in rows:
                if q == match[0]:
                    return q, a
    return None, None

def export_to_json():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT question, answer FROM memory")
        data = [{"question": q, "answer": a} for q, a in cur.fetchall()]
        with open(BACKUP_FILE, "w") as f:
            json.dump(data, f, indent=2)
    log_info("Memory exported to JSON.")

# === BOT SETUP ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(msg: Message):
    log_info(f"/start from {msg.from_user.id}")
    await msg.answer(
        "<b>🤖 Welcome!</b>\n"
        "I’m a self-learning bot.\n"
        "Ask me anything. If I don’t know, reply to teach me!"
    )

@dp.message()
async def handle_msg(msg: Message):
    try:
        log_info(f"Received: '{msg.text}' from {msg.from_user.id}")

        if msg.reply_to_message and msg.reply_to_message.text.startswith("❓ I don't know yet:"):
            question = msg.reply_to_message.text.replace("❓ I don't know yet:", "").strip()
            answer = msg.text.strip()
            save_memory(question, answer)
            await msg.answer("✅ Got it! I’ve learned your response.")
        else:
            question = msg.text.strip()
            matched_q, answer = get_answer(question)
            if answer:
                await msg.answer(f"💡 {answer}")
            else:
                await msg.answer(f"❓ I don't know yet: {question}\nReply to this message with the correct answer to teach me.")
    except Exception as e:
        log_error(f"❌ Error in message handler: {e}")

# === MAIN LOOP ===
async def main():
    log_info("Starting bot...")
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
