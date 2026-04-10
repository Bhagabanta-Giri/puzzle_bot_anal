import os
import json
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

def load_puzzles():
    with open('puzzles.json', 'r') as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Shakuntala Devi Challenge! \n\nUse /puzzle to get a new math problem."
    )

async def send_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puzzles = load_puzzles()
    puzzle = random.choice(puzzles)
    
    context.user_data['current_puzzle'] = puzzle
    
    message = f"<b>Puzzle #{puzzle['id']}</b>\n\n{puzzle['question']}"
    
    keyboard = [[InlineKeyboardButton("Reveal Answer", callback_data='reveal')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

async def reveal_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    puzzle = context.user_data.get('current_puzzle')
    
    if puzzle:
        response = (
            f" <b>Answer:</b> {puzzle['answer']}\n\n"
            f" <b>Explanation:</b> {puzzle['explanation']}\n\n"
            f" <b>Pitfall:</b> {puzzle['pitfalls']}"
        )
        
        full_text = f"{query.message.text}\n\n{response}"
        
        await query.edit_message_text(text=full_text, parse_mode='HTML')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('puzzle', send_puzzle))
    app.add_handler(CallbackQueryHandler(reveal_answer, pattern='reveal'))
    
    print("Bot is running with puzzles...")
    app.run_polling()