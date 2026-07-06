"""
Run with: python bot.py
"""
import asyncio
import datetime
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

import config
import db
from content_gen import generate_quiz_content
from notebook_image import render_notebook_image
from leaderboard import build_leaderboard_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("quizbot")

OPTION_LETTERS = ["A", "B", "C", "D"]
TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)


def build_answer_keyboard(question_id, options):
    row = []
    for i, opt in enumerate(options):
        letter = OPTION_LETTERS[i]
        row.append(InlineKeyboardButton(f"{letter}. {opt}", callback_data=f"ans:{question_id}:{letter}"))
    return InlineKeyboardMarkup([[b] for b in row])


async def post_daily_quiz(app: Application):
    try:
        content = generate_quiz_content()
    except Exception:
        log.exception("Content generation failed, skipping this run")
        return

    topic = content["topic"]
    set_id = db.create_quiz_set(topic)

    img_path = os.path.join(TMP_DIR, f"notes_{set_id}.png")
    render_notebook_image(topic, content["notes"], img_path)

    caption = (
        f"📘 <b>{topic} — Advanced English Grammar Notes</b>\n\n"
        f"Master {topic.lower()} with today's advanced guide. Test yourself below with "
        f"5 hard MCQs and see how you rank against other learners!\n\n"
        f"#EnglishGrammar #{topic.replace(' ', '')} #LearnEnglish #ESL #GrammarQuiz"
    )
    with open(img_path, "rb") as photo:
        await app.bot.send_photo(chat_id=config.CHANNEL_USERNAME, photo=photo, caption=caption,
                                  parse_mode=ParseMode.HTML)

    for q in content["questions"]:
        correct_letter = OPTION_LETTERS[q["correct_index"]]
        question_id = db.add_question(
            set_id=set_id,
            question_text=q["question"],
            options=q["options"],
            correct_option=correct_letter,
        )
        keyboard = build_answer_keyboard(question_id, q["options"])
        text = f"🧠 <b>Hard Question — {topic}</b>\n\n{q['question']}\n\n👥 0 people have answered so far."
        msg = await app.bot.send_message(
            chat_id=config.CHANNEL_USERNAME, text=text,
            parse_mode=ParseMode.HTML, reply_markup=keyboard,
        )
        db.set_question_message_id(question_id, msg.message_id)

    os.remove(img_path)
    log.info("Posted quiz set for topic: %s", topic)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db.upsert_user(user.id, user.username, user.first_name)

    try:
        _, question_id_str, chosen_letter = query.data.split(":")
        question_id = int(question_id_str)
    except ValueError:
        await query.answer("Invalid answer data.", show_alert=False)
        return

    if db.has_answered(question_id, user.id):
        await query.answer("You've already answered this question. It can only be answered once!",
                            show_alert=True)
        return

    question = db.get_question(question_id)
    if not question:
        await query.answer("This question no longer exists.", show_alert=True)
        return

    is_correct = (chosen_letter == question["correct_option"])
    db.record_answer(question_id, user.id, chosen_letter, is_correct)

    if is_correct:
        await query.answer("✅ Correct! Well done.", show_alert=True)
    else:
        correct_text = question[f"option_{question['correct_option'].lower()}"]
        await query.answer(
            f"❌ Not quite. Correct answer: {question['correct_option']}. {correct_text}",
            show_alert=True,
        )

    total = db.count_answers(question_id)
    topic_line = query.message.text.split("\n")[0] if query.message.text else ""
    new_text = f"{topic_line}\n\n{question['question_text']}\n\n👥 {total} people have answered so far."
    try:
        await query.edit_message_text(
            text=new_text,
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup,
        )
    except Exception:
        pass


async def post_monthly_leaderboard(app: Application):
    now = datetime.datetime.utcnow()
    first_of_this_month = now.replace(day=1)
    last_month_end = first_of_this_month - datetime.timedelta(days=1)
    year_month = last_month_end.strftime("%Y-%m")
    month_label = last_month_end.strftime("%B %Y")

    text = build_leaderboard_message(year_month, month_label)
    await app.bot.send_message(chat_id=config.CHANNEL_USERNAME, text=text, parse_mode=ParseMode.HTML)
    log.info("Posted leaderboard for %s", year_month)


async def main():
    db.init_db()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^ans:"))

    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    for t in config.POST_TIMES:
        hour, minute = [int(x) for x in t.split(":")]
        scheduler.add_job(post_daily_quiz, CronTrigger(hour=hour, minute=minute), args=[app])

    scheduler.add_job(post_monthly_leaderboard, CronTrigger(day=1, hour=0, minute=5), args=[app])
    scheduler.start()

    log.info("Bot started. Scheduled post times: %s (%s)", config.POST_TIMES, config.TIMEZONE)

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
