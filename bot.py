import os
import requests
import re
import logging

from cache import Cache

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

WORKSPACE_ID = os.environ.get('WORKSPACE_ID')
ALLOWED_USERS = os.environ.get('ALLOWED_USERS').split(',')
ASSEMBLA_API_BASE = 'https://api.assembla.com/'

ASSEMBLA_HEADERS = {
    'X-Api-Key': os.environ.get('ASSEMBLA_KEY'),
    'X-Api-Secret': os.environ.get('ASSEMBLA_SECRET'),
    'Content-Type': 'application/json',
}

STATUS_BUTTONS = {
    749754: 'New',
    749756: 'Development',
    3774573: 'Test.ppj',
}

cache = Cache()

def _fetch_cached(url, timeout=60):
    cached = cache.get(url)
    if cached:
        return cached

    response = requests.get(url, headers=ASSEMBLA_HEADERS)
    logging.info('Cache Miss: {}'.format(url))

    if response.status_code == 200:
        data = response.json()
        cache.set(url, data, timeout)
        return data


def _fetch_users():
    users = _fetch_cached(
        f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/users',
        600
    )

    return {u['id']: u['name'] for u in users}


def _fetch_milestones():
    return _fetch_cached(
        f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/milestones',
    )


def _fetch_ticket_info(ticket_id: int):
    return _fetch_cached(
        f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/tickets/{ticket_id}',
    )


def _get_ticket_message(ticket):
    number = ticket.get('number')
    summary = ticket.get('summary')
    description = ticket.get('description')
    status = ticket.get('status')
    assembla_users = _fetch_users()
    user = assembla_users.get(ticket.get('assigned_to_id'), '')

    print(ticket)

    return f"""
<strong>#{number} {summary}</strong>
<pre>{description}</pre>
<code>{status}</code> {user}
"""

def _get_ticket_id(url: str):
    match = re.search(r'ticket=(\d+)|tickets\/(\d+)', url)

    if match:
        group = [g for g in match.groups() if g]
        if len(group):
            return group[0]


def _render_ticket_info(update, context, ticket_id):
    if not ticket_id:
        return

    ticket = _fetch_ticket_info(int(ticket_id))
    keyboard = []
    for status_id in STATUS_BUTTONS:
        print(status_id, ticket.get('status'))
        if status_id != ticket.get('status'):
            keyboard.append(
                InlineKeyboardButton(
                    STATUS_BUTTONS[status_id],
                    callback_data=f'{ticket_id},{status_id}'
                )
            )

    logging.info(f'Ticket Reply {update.message.from_user.username} {ticket_id}')
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
        logging.warn(f'Unknown User: {update.message.from_user.username}')
        return False


def links(update, context):
    if not _is_valid_user(update):
        return None

    text = update.message.text
    url_entities = [x for x in update.message.entities if x['type'] == 'url']
    ticket_urls = []

    for entity in url_entities:
        url = text[entity.offset:entity.offset+entity.length]
        if 'ticket=' in url or 'tickets/' in url:
            ticket_urls.append(url)

    for url in ticket_urls:
        ticket_id = _get_ticket_id(url)
        _render_ticket_info(update, context, ticket_id)

def start(update, context):
    if not _is_valid_user(update):
        return None

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello! Paste an assembla ticket link to get started!'
    )


def sprint(update, context):
    if not _is_valid_user(update):
        return None

    milestones = _fetch_milestones()
    if len(milestones):
        title = milestones[0].get('title')
        branch = title.replace(' ', '-').lower()
        start_date = milestones[0].get('start_date')
        text = f'{title} ({start_date})  -  <code>{branch}</code>'
    else:
        text = 'No Active sprint'

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


def ticket(update, context):
    if not _is_valid_user(update):
        return None

    match = re.search('\d+', update.message.text)
    if not match:
        return None

    _render_ticket_info(update, context, match.group(0))


def button(update, context):
    query = update.callback_query
    ticket_id, status_id = query.data.split(',')

    url = f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/tickets/{ticket_id}'
    data = {
        'ticket': {
            'status': status_id
        }
    }
    response = requests.put(
        url, json=data, headers=ASSEMBLA_HEADERS
    )


def main():
    logging.info('Launching')

    updater = Updater(token=os.environ.get('TELEGRAM_TOKEN'), use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(CommandHandler('sprint', sprint))
    dispatcher.add_handler(CommandHandler('ticket', ticket))

    link_handler = MessageHandler(Filters.all, links)
    dispatcher.add_handler(link_handler)

    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()


if __name__ == '__main__':
    main()
