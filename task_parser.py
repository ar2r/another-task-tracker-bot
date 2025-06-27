import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def extract_jira_ticket(text: str) -> Optional[str]:
    """Extract Jira ticket number from URL or text"""
    # Pattern for Jira URLs: https://domain.com/browse/TICKET-123
    jira_url_pattern = r'https?://[^/]+/browse/([A-Z]+-\d+)'
    match = re.search(jira_url_pattern, text)
    
    if match:
        return match.group(1)
    
    # Pattern for standalone ticket: TICKET-123
    ticket_pattern = r'\b([A-Z]+-\d+)\b'
    match = re.search(ticket_pattern, text)
    
    if match:
        return match.group(1)
    
    return None

def parse_task_message(message: str) -> Tuple[str, Optional[str], bool]:
    """
    Parse task message to extract task name and comment
    Returns (task_name, comment, is_jira_link)
    """
    message = message.strip()
    
    # Check if it's a Jira URL
    jira_url_pattern = r'https?://[^/]+/browse/[A-Z]+-\d+'
    if re.match(jira_url_pattern, message.split()[0]):
        parts = message.split(' ', 1)
        jira_url = parts[0]
        comment = parts[1] if len(parts) > 1 else None
        return jira_url, comment, True
    
    # Check for single word task (no spaces) or extract first word
    parts = message.split(' ', 1)
    task_name = parts[0].lower()  # Convert to lowercase as specified
    comment = parts[1] if len(parts) > 1 else None
    
    # Check if task name looks like a Jira ticket
    ticket_number = extract_jira_ticket(task_name)
    is_jira = ticket_number is not None
    
    return task_name, comment, is_jira

def format_task_for_display(task_name: str, is_jira: bool = None) -> str:
    """Format task name for display in messages"""
    if is_jira is None:
        is_jira = extract_jira_ticket(task_name) is not None
    
    if is_jira:
        # If it's a Jira URL, extract ticket number for display
        if task_name.startswith('http'):
            ticket = extract_jira_ticket(task_name)
            if ticket:
                return f"[{ticket}]({task_name})"
        else:
            # If it's just a ticket number, make it a placeholder link
            ticket = extract_jira_ticket(task_name)
            if ticket:
                return f"`{ticket}`"
    
    return f"`{task_name}`"

def get_unique_comments(tasks) -> list:
    """Get unique comments from a list of tasks"""
    comments = set()
    for task in tasks:
        if task.comment and task.comment.strip():
            comments.add(task.comment.strip())
    
    return sorted(list(comments))
