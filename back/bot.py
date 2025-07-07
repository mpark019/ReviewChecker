import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()

TOKEN = os.getenv("SLACK_TOKEN")
if not TOKEN:
    raise RuntimeError("Set SLACK_TOKEN in your .env")


client = slack.WebClient(TOKEN)

# client.chat_postMessage(channel='#pigglytest', text="test")

SCHEDULED_MESSAGES = [
    {'text': 'First Message', 'post_at': (datetime.now() + timedelta(seconds=10)).timestamp(), 'channel':'C093GDNKJ04'},
]

def schedule_message(messages):
    ids = []
    for msg in messages:
        response = client.chat_schedulemessage(channel=msg['channel'], text=msg['text'], post_at=msg['post_at'])

    id_ = response.get('id')
    ids.append(id_)
