import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from aiogram.client.default import DefaultBotProperties
from colorama import Fore, Style, init as colorama_init
import difflib

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 5290407067
MEMORY_FILE = "memory.json"

# === INIT COLOR LOG ===
colorama_init(autoreset=True)
def log_info(msg): print(Fore.CYAN + "[INFO] " + Style.RESET_ALL + msg)
def log_success(msg): print(Fore.GREEN + "[SUCCESS] " + Style.RESET_ALL + msg)
def log_warn(msg): print(Fore.YELLOW + "[WARNING] " + Style.RESET_ALL + msg)
def log_error(msg): print(Fore.RED + "[ERROR] " + Style.RESET_ALL + msg)

# === MEMORY ===
memory = {}

def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
        log_success(f"Loaded {len(memory)} items from memory.json")
    else:
        memory = {}
        log_warn("memory.json not found. Starting fresh.")

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)
    log_info(f"Saved memory.json with {len(memory)} items")

def learn(question: str, answer: str):
    memory[question] = answer
    save_memory()

def get_answer(user_input: str):
    questions = list(memory.keys())
    matches = difflib.get_close_matches(user_input, questions, n=1, cutoff=0.6)
    return memory.get(matches[0]) if matches else None

# === BOT SETUP ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await msg.answer(
        "<b>🤖 Self-learning Bot Ready!</b>\n"
        "Ask me anything. If I don’t know, reply with the correct answer to teach me."
    )

@dp.message(Command("export"))
async def export_cmd(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("🚫 You're not authorized to use this command.")
    
    try:
        file = FSInputFile(MEMORY_FILE)
        await msg.answer_document(file, caption="🧠 Full learned memory")
        log_info("Exported memory.json to owner.")
    except Exception as e:
        log_error(f"❌ Failed to export: {e}")
        await msg.answer("⚠️ Failed to export memory.")

@dp.message()
async def handle_msg(msg: Message):
    try:
        log_info(f"Received: {msg.text}")
        if msg.reply_to_message and msg.reply_to_message.text.startswith("❓ I don't know yet:"):
            question = msg.reply_to_message.text.replace("❓ I don't know yet:", "").strip()
            answer = msg.text.strip()
            learn(question, answer)
            await msg.answer("✅ Learned! Thanks.")
        else:
            question = msg.text.strip()
            answer = get_answer(question)
            if answer:
                await msg.answer(f"💡 {answer}")
            else:
                await msg.answer(f"❓ I don't know yet: {question}\nReply to this message with the correct answer to teach me.")
    except Exception as e:
        log_error(f"❌ Handler error: {e}")

# === MAIN ===
async def main():
    log_info("Starting bot...")
    load_memory()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
