import os
import requests
import re
import logging

from cached import fetch_cached

JIRA_API_BASE = "https://veremark.atlassian.net/rest/api/2/"
JIRA_HEADERS = {"Authorization": f"Basic {os.environ.get('JIRA_KEY')}"}


def get_ticket_id(url: str):
    match = re.search(r"selectedIssue=APP-(\d+)|APP-(\d+)", url)

    if match:
        group = [g for g in match.groups() if g]
        if len(group):
            return f"APP-{group[0]}"


def fetch_ticket_by_id(ticket_id: str) -> dict:
    issue = fetch_cached(f"{JIRA_API_BASE}issue/{ticket_id}", JIRA_HEADERS)
    fields = issue["fields"]

    return {
        "id": ticket_id,
        "user": fields["assignee"]["displayName"],
        "number": ticket_id,
        "description": fields["description"],
        "summary": fields["summary"],
        "status": fields["status"]["name"],
    }


def fetch_ticket_from_link(link: str) -> dict:
    return fetch_ticket_by_id(get_ticket_id(link))
