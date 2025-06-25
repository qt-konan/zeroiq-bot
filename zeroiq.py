import os
import json
import asyncio
import difflib
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from aiogram.client.default import DefaultBotProperties
from colorama import Fore, Style, init as colorama_init

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
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
        log_success(f"Loaded {len(memory)} entries from memory.json")
    else:
        memory = {}
        log_warn("memory.json not found. Starting fresh.")

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
    log_info(f"Saved memory.json with {len(memory)} entries")

def learn(question: str, answer: str):
    memory[question.strip()] = answer.strip()
    save_memory()

def get_answer(user_input: str):
    questions = list(memory.keys())
    matches = difflib.get_close_matches(user_input, questions, n=1, cutoff=0.6)
    return memory.get(matches[0]) if matches else None

# === BOT SETUP ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "<b>🤖 Welcome to the self-learning bot!</b>\n"
        "Ask me anything. If I don’t know, reply to my message with the correct answer to teach me."
    )

@dp.message(Command("export"))
async def cmd_export(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("🚫 You're not allowed to do this.")
    try:
        file = FSInputFile(MEMORY_FILE)
        await msg.answer_document(file, caption="🧠 Here's the full learned memory")
        log_info("Memory exported to owner.")
    except Exception as e:
        log_error(f"Export failed: {e}")
        await msg.answer("⚠️ Failed to export memory.")

@dp.message()
async def msg_handler(msg: Message):
    try:
        user_input = msg.text.strip()
        log_info(f"User said: {user_input}")

        # Learn response if replying to bot's unknown message
        if msg.reply_to_message:
            original = msg.reply_to_message.text or ""
            if "I don't know yet:" in original:
                question = original.split("I don't know yet:")[-1].strip()
                learn(question, user_input)
                await msg.answer("✅ Learned! Thank you.")
                return

        # Normal response
        answer = get_answer(user_input)
        if answer:
            await msg.answer(f"💡 {answer}")
        else:
            await msg.answer(f"❓ I don't know yet: {user_input}\nReply to this message with the correct answer to teach me.")
    except Exception as e:
        log_error(f"Handler error: {e}")

# === MAIN ===
async def main():
    log_info("Bot starting...")
    load_memory()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
