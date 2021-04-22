import os
import requests
import re
import logging

import assembla
import jira

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

ALLOWED_USERS = os.environ.get("ALLOWED_USERS", "").split(",")


def _get_ticket_message(ticket):
    number = ticket.get("number")
    summary = ticket.get("summary")
    description = ticket.get("description")
    status = ticket.get("status")
    user = ticket.get("user")

    return f"""
<strong>{number} {summary}</strong>
<pre>{description}</pre>
<code>{status}</code> {user}
"""


def render_ticket(update, context, ticket: dict):
    logging.info(f"Ticket Reply {update.message.from_user.username} {ticket['id']}")
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=_get_ticket_message(ticket),
        parse_mode=ParseMode.HTML,
    )


def _is_valid_user(update):
    user = update.message.from_user
    if user.username in ALLOWED_USERS or str(user.id) in ALLOWED_USERS:
        return True
    else:
        logging.warning(f"Unknown User: {update.message.from_user.username}")
        return False


def links(update, context):
    if not _is_valid_user(update):
        return None

    text = update.message.text
    url_entities = [x for x in update.message.entities if x["type"] == "url"]
    assembla_urls = []

    jira_urls = []

    for entity in url_entities:
        url = text[entity.offset : entity.offset + entity.length]

        # Assembla
        if "ticket=" in url or "tickets/" in url:
            assembla_urls.append(url)

        # Jira
        if "browse/APP-" in url:
            jira_urls.append(url)

    for url in assembla_urls:
        render_ticket(update, context, assembla.fetch_ticket_from_link(url))

    for url in jira_urls:
        render_ticket(update, context, jira.fetch_ticket_from_link(url))


def start(update, context):
    if not _is_valid_user(update):
        return None

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello! Paste an assembla ticket link to get started!",
    )


def sprint(update, context):
    if not _is_valid_user(update):
        return None

    milestones = assembla.fetch_milestones()
    if len(milestones):
        title = milestones[0].get("title")
        branch = title.replace(" ", "-").lower()
        start_date = milestones[0].get("start_date")
        text = f"{title} ({start_date})  -  <code>{branch}</code>"
    else:
        text = "No Active sprint"

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


def main():
    logging.info("Launching")

    updater = Updater(token=os.environ.get("TELEGRAM_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(CommandHandler("sprint", sprint))

    link_handler = MessageHandler(Filters.all, links)
    dispatcher.add_handler(link_handler)

    updater.start_polling()


if __name__ == "__main__":
    main()
