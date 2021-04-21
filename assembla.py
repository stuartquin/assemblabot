import os
import re
import logging
from cached import fetch_cached

WORKSPACE_ID = os.environ.get("WORKSPACE_ID")
ASSEMBLA_API_BASE = "https://api.assembla.com/"

ASSEMBLA_HEADERS = {
    "X-Api-Key": os.environ.get("ASSEMBLA_KEY"),
    "X-Api-Secret": os.environ.get("ASSEMBLA_SECRET"),
    "Content-Type": "application/json",
}


def get_ticket_id(url: str):
    match = re.search(r"ticket=(\d+)|tickets\/(\d+)", url)

    if match:
        group = [g for g in match.groups() if g]
        if len(group):
            return group[0]


def fetch_users():
    users = fetch_cached(
        f"{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/users", ASSEMBLA_HEADERS, 600
    )
    return {u["id"]: u["name"] for u in users}


def fetch_milestones():
    return fetch_cached(
        f"{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/milestones", ASSEMBLA_HEADERS
    )


def fetch_ticket(ticket_id: int):
    return fetch_cached(
        f"{ASSEMBLA_API_BASE}v1/spaces/{WORKSPACE_ID}/tickets/{ticket_id}",
        ASSEMBLA_HEADERS,
    )


def fetch_ticket_from_link(link: str) -> dict:
    ticket = fetch_ticket(get_ticket_id(link))
    users = fetch_users()
    ticket["user"] = users.get(ticket.get("assigned_to_id"), "")
    return ticket
