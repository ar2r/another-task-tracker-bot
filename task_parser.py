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
    if not message:
        return "", None, False
        
    message = message.strip()
    
    # Check if message contains Jira ticket or URL
    jira_ticket = extract_jira_ticket(message)
    if jira_ticket:
        # If it's a Jira URL, extract ticket and comment
        if message.startswith('http'):
            parts = message.split(' - ', 1) if ' - ' in message else message.split(' ', 1)
            comment = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
            return jira_ticket, comment, True
        else:
            # If message contains Jira ticket, extract it and comment
            if ' - ' in message:
                parts = message.split(' - ', 1)
                comment = parts[1].strip() if len(parts) > 1 else None
            else:
                # Find position of ticket and get everything after it as comment
                ticket_match = re.search(r'\b([A-Z]+-\d+)\b', message)
                if ticket_match:
                    start_pos = ticket_match.end()
                    remaining = message[start_pos:].strip()
                    comment = remaining[1:].strip() if remaining.startswith('-') else (remaining if remaining else None)
                else:
                    comment = None
            return jira_ticket, comment, True
    
    # Parse regular task with optional comment (separated by ' - ')
    if ' - ' in message:
        parts = message.split(' - ', 1)
        task_name = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else None
    else:
        task_name = message.strip()
        comment = None
    
    return task_name, comment, False

def format_task_for_display(task_name: str, is_jira: bool = None) -> str:
    """Format task name for display in messages"""
    if is_jira is None:
        is_jira = extract_jira_ticket(task_name) is not None
    
    # Always use markdown bold formatting for tasks
    return f"**{task_name}**"

def get_unique_comments(tasks) -> list:
    """Get unique comments from a list of tasks"""
    comments = set()
    for task in tasks:
        if task.comment and task.comment.strip():
            comments.add(task.comment.strip())
    
    return sorted(list(comments))
