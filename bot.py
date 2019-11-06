import os
import requests
import re
import logging
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

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
}

def _fetch_users():
    response = requests.get(
        f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/users',
        headers=ASSEMBLA_HEADERS,
    )

    if response.status_code == 200:
        return {u['id']: u['name'] for u in response.json()}

ASSEMBLA_USERS = _fetch_users()


def _fetch_ticket_info(ticket_id: int):
    response = requests.get(
        f'{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/tickets/{ticket_id}',
        headers=ASSEMBLA_HEADERS,
    )

    if response.status_code == 200:
        return response.json()


def _get_ticket_message(ticket):
    number = ticket.get('number')
    summary = ticket.get('summary')
    description = ticket.get('description')
    status = ticket.get('status')
    user = ASSEMBLA_USERS.get(ticket.get('assigned_to_id'), '')

    return f"""
<strong>#{number} {summary}</strong>
<pre>{description}</pre>
<code>{status}</code> {user}
"""


def _handle_ticket_url(url: str):
    match = re.search(r'ticket=(\d+)|tickets\/(\d+)', url)

    if match:
        group = [g for g in match.groups() if g]
        if len(group):
            ticket = _fetch_ticket_info(int(group[0]))
            if ticket:
                return _get_ticket_message(ticket)


def _is_valid_user(update):
    user = update.message.from_user
    print('User', user)
    if user.username in ALLOWED_USERS or user.id in ALLOWED_USERS:
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
        message = _handle_ticket_url(url)
        if message:
            logging.info(f'Ticket Reply {update.message.from_user.username}')
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode=ParseMode.HTML
            )

def start(update, context):
    if not _is_valid_user(update):
        return None

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello! Paste an assembla ticket link to get started!'
    )


def main():
    logging.info('Launching')

    updater = Updater(token=os.environ.get('TELEGRAM_TOKEN'), use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    link_handler = MessageHandler(Filters.all, links)
    dispatcher.add_handler(link_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
