import requests
import feedparser  # backup, needs no key
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= HOW TO GET TELEGRAM_CHAT_ID =================
# 1. Create bot with @BotFather -> get TELEGRAM_TOKEN
# 2. Send ANY message to your bot (like "hi")
# 3. Open this link in browser (replace <TOKEN>):
#    https://api.telegram.org/bot<TOKEN>/getUpdates
# 4. Find "chat":{"id": 123456789 } -> That's your CHAT_ID
# ===============================================================

SUBREDDITS = ['AmITheAsshole', 'confession', 'RelationshipIndia', 'AskIndia']
HEADERS = {'User-Agent': 'viralbot_arun56333 by u/arun56333'}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def create_image(text, title="Viral Story"):
    # Step 2: Make Instagram post image (1080x1350)
    W, H = 1080, 1350
    img = Image.new('RGB', (W, H), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 52)
        font_text = ImageFont.truetype("arial.ttf", 36)
        font_footer = ImageFont.truetype("arial.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # Draw title
    y = 80
    title_lines = textwrap.wrap(title, width=28)
    for line in title_lines[:3]:
        draw.text((60, y), line, font=font_title, fill='black')
        y += 65

    y += 30
    draw.line([(60, y), (W-60, y)], fill="#eeeeee", width=2)
    y += 40

    # Draw body text
    wrapped = textwrap.wrap(text, width=40)
    for line in wrapped[:16]:  # limit to fit card
        draw.text((60, y), line, font=font_text, fill='#111111')
        y += 50

    # Footer watermark
    draw.text((60, H-80), "@arun56333 • NO API • FREE FOREVER", font=font_footer, fill='#999999')
    draw.text((W-220, H-80), "r/" + "viral", font=font_footer, fill='#dddddd')

    path = "/tmp/viral_post.png"
    img.save(path)
    return path

def get_viral_post():
    # Step 1: Get viral post from subreddit WITHOUT PERMISSION
    # This is like reading a public newspaper - no login needed!
    best_post = None
    best_score = 0
    random.shuffle(SUBREDDITS)

    for sub in SUBREDDITS:
        try:
            # Method 1: JSON - needs only User-Agent, NO client_id
            url = f'https://www.reddit.com/r/{sub}/top.json?limit=10&t=day'
            r = requests.get(url, headers=HEADERS, timeout=12)
            data = r.json()
            posts = data['data']['children']

            for p in posts:
                d = p['data']
                # Filter only viral stories
                if d['score'] > 8000 and d['score'] > best_score:
                    if len(d.get('selftext','')) > 120:
                        best_score = d['score']
                        best_post = {
                            'title': d['title'],
                            'text': d['selftext'][:1200],
                            'score': d['score'],
                            'subreddit': sub,
                            'url': 'https://reddit.com' + d['permalink']
                        }
        except Exception as e:
            print(f"JSON failed for r/{sub}, trying RSS: {e}")
            # Method 2: RSS - 100% public, works even if JSON blocked
            try:
                rss_url = f'https://www.reddit.com/r/{sub}/top.rss?t=day'
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    entry = feed.entries[0]
                    if best_post is None:
                        best_post = {
                            'title': entry.title,
                            'text': entry.get('summary','')[:1200] or entry.title,
                            'score': 9999,
                            'subreddit': sub,
                            'url': entry.link
                        }
            except Exception as e2:
                print(f"RSS also failed: {e2}")
                continue

    return best_post

# Telegram Bot Logic

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 NO-API Viral Bot by @arun56333\n\n"
        "This bot needs NO Reddit permission!\n"
        "Commands:\n"
        "/test - Get viral post now\n"
        "Auto-check every 30 mins"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Hunting viral posts (no API key)...")
    post = get_viral_post()

    if not post:
        await update.message.reply_text("No viral post found (>8000 upvotes). Try again later.")
        return

    image_path = create_image(post['text'], post['title'])
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve & Post", callback_data=f"approve|{post['url']}"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"🔥 *{post['title']}*\n\n"               f"r/{post['subreddit']} • {post['score']} upvotes\n"               f"{post['url']}"

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(image_path, 'rb'),
        caption=caption,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("approve"):
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ APPROVED - Ready to post to Insta!",
            parse_mode='Markdown'
        )
        # Here you add your Instagram posting logic
    else:
        await query.edit_message_caption(
            caption="⏭️ Skipped. Waiting for next viral post...",
        )

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    # Step 3: Background job every 30 mins
    print("⏰ Auto-checking viral posts...")
    post = get_viral_post()
    if not post:
        return

    image_path = create_image(post['text'], post['title'])
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve|{post['url']}"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"🚀 Auto-found viral post!\n\n"               f"🔥 *{post['title']}*\n"               f"r/{post['subreddit']} • {post['score']} upvotes"

    await context.bot.send_photo(
        chat_id=TELEGRAM_CHAT_ID,
        photo=open(image_path, 'rb'),
        caption=caption,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Run every 30 mins = 1800 seconds
    app.job_queue.run_repeating(auto_job, interval=1800, first=10)

    print("🤖 NO-API Bot started by @arun56333 - No Reddit permission needed!")
    app.run_polling()

if __name__ == "__main__":
    main()
