import os
import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

def fetch_live_random_puzzle():
    random_days_back = random.randint(1, 90)
    target_date = datetime.now() - timedelta(days=random_days_back)
    date_str = target_date.strftime("%Y%m%d")
    
    url = f"https://www.brainbashers.com/dailypuzzle.asp?date={date_str}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    print(f"Scraping: Fetching archive date {date_str}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')

        def clean_node_text(node):
            if isinstance(node, str):
                return node
            
            for bold in node.find_all(['strong', 'b']):
                bold.replace_with(f"*{bold.get_text(strip=True)}*")
            for br in node.find_all('br'):
                br.replace_with("\n")
                
            text = node.get_text()
            text = text.replace('\xa0', ' ').replace('\r', '')
            return text

        # --- 1. QUESTION EXTRACTION ---
        q_start = soup.find(string=lambda text: isinstance(text, Comment) and 'Question Start' in text)
        q_end = soup.find(string=lambda text: isinstance(text, Comment) and 'Question End' in text)
        
        question_text = ""
        if q_start and q_end:
            collected_q = []
            next_node = q_start.next_sibling
            while next_node and next_node != q_end:
                if next_node.name:  # Only parse valid HTML tags, skip raw string newlines
                    collected_q.append(clean_node_text(next_node).strip())
                next_node = next_node.next_sibling
            question_text = "\n".join([q for q in collected_q if q])

        # --- 2. HINT EXTRACTION ---
        hint_div = soup.find('div', id='hdivans')
        hint_text = "No hint available for this puzzle."
        if hint_div:
            hint_text = clean_node_text(hint_div).replace("Hints", "", 1).strip()

        # --- 3. ANSWER/SOLUTION EXTRACTION ---
        s_start = soup.find(string=lambda text: isinstance(text, Comment) and 'Answer Start' in text)
        s_end = soup.find(string=lambda text: isinstance(text, Comment) and 'Answer End' in text)
        
        answer_text = ""
        if s_start and s_end:
            collected_s = []
            next_node = s_start.next_sibling
            while next_node and next_node != s_end:
                if next_node.name:
                    collected_s.append(clean_node_text(next_node).strip())
                next_node = next_node.next_sibling
            
            raw_ans = "\n".join([s for s in collected_s if s])
            answer_text = raw_ans.strip()

        answer = {
            "question": question_text,
            "hint": hint_text,
            "answer": answer_text
        }
        
        return answer

    except Exception as e:
        print(f"Live scraping error: {e}")
        return None
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Welcome to Shakuntala Puzzle Bot!*\n\n"
        "Send /puzzle to pull a live riddle instantly from the archive.",
        parse_mode="Markdown"
    )

async def send_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    
    puzzle = fetch_live_random_puzzle()
    
    if not puzzle:
        puzzle = fetch_live_random_puzzle()
        
    if not puzzle:
        await update.message.reply_text("Connection timeout gathering puzzle. Please try again!")
        return

    chat_id = update.effective_chat.id
    context.bot_data[f"{chat_id}_hint"] = puzzle["hint"]
    context.bot_data[f"{chat_id}_answer"] = puzzle["answer"]

    keyboard = [
        [
            InlineKeyboardButton("Reveal Hint", callback_data="show_hint"),
            InlineKeyboardButton("Show Solution", callback_data="show_solution")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"*BrainBashers Daily Challenge*\n\n{puzzle['question']}",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id

    if query.data == "show_hint":
        hint = context.bot_data.get(f"{chat_id}_hint", "No hint data found.")
        await query.message.reply_text(f"*Hint:*\n{hint}", parse_mode="Markdown")
        
    elif query.data == "show_solution":
        answer = context.bot_data.get(f"{chat_id}_answer", "No solution data found.")
        await query.message.reply_text(f"*Solution Details:*\n\n{answer}", parse_mode="Markdown")

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN missing from .env file!")
        return

    print("Launching Live-Extraction Telegram Bot...")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("puzzle", send_puzzle))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    app.run_polling()

if __name__ == "__main__":
    main()