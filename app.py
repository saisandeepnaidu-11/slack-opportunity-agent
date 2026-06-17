import os
import re
import json
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Local modules
from search_client import RealTimeSearchClient
from matcher import OpportunityMatcher
from slack_helper import SlackMessageGenerator

# Load configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bolt App
# By default, uses Socket Mode which requires SLACK_APP_TOKEN and SLACK_BOT_TOKEN
bot_token = os.getenv("SLACK_BOT_TOKEN")
signing_secret = os.getenv("SLACK_SIGNING_SECRET")

token_verification = True
if not bot_token or bot_token == "xoxb-mock-token":
    bot_token = "xoxb-mock-token"
    token_verification = False

if not signing_secret:
    signing_secret = "mock-signing-secret"

app = App(
    token=bot_token,
    signing_secret=signing_secret,
    token_verification_enabled=token_verification
)

# Initialize API clients and engines
search_client = RealTimeSearchClient()
matcher = OpportunityMatcher()

@app.event("app_mention")
def handle_app_mentions(event, say, client):
    """
    Responds when the bot is mentioned. Performs a search for opportunities matching 
    the caller's user profile and sends customized recommendations.
    """
    user_id = event.get("user")
    channel_id = event.get("channel")
    text = event.get("text", "")
    
    logger.info(f"Received mention from user {user_id} in channel {channel_id} with text: {text}")
    
    # 1. Look up user profile
    user_profile = next((p for p in matcher.profiles if p["id"] == user_id), None)
    if not user_profile:
        # Fallback profile if caller is not in preconfigured beneficiary list
        user_profile = {
            "id": user_id,
            "name": f"<@{user_id}>",
            "skills": ["computer science", "python", "education"],
            "location": "Andhra Pradesh",
            "interests": ["scholarship", "training"],
            "slack_channel": channel_id
        }
    
    # 2. Extract query keywords from mention or default
    query = "scholarships jobs initiatives"
    import re as _re
    clean_text = _re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    if clean_text:
        query = clean_text

    # 3. Fetch opportunities
    opportunities = search_client.fetch_opportunities(query)
    
    # 4. Perform matching
    temp_matcher = OpportunityMatcher(profiles=[user_profile])
    matches = []
    for opp in opportunities:
        matches.extend(temp_matcher.match_opportunity(opp))
        
    if not matches:
        say("❌ No matching opportunities found right now. I'll continue monitoring public sources and alert you!")
        return
        
    # 5. Send top matches (limit to 3 messages to avoid spamming)
    # The first message combines the summary header and the first card.
    for i, match in enumerate(matches[:3]):
        payload = SlackMessageGenerator.build_opportunity_block(match)
        blocks = payload["blocks"]
        if i == 0:
            summary_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎉 Found *{len(matches)}* matching opportunities for you!"
                }
            }
            blocks = [summary_block, {"type": "divider"}] + blocks

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"New Opportunity: {match['opportunity']['title']}"
        )

@app.command("/find-opportunities")
def handle_find_command(ack, body, client):
    """
    Slash command /find-opportunities to trigger search manually.
    """
    ack()
    user_id = body.get("user_id")
    channel_id = body.get("channel_id")
    command_text = body.get("text", "")
    
    logger.info(f"Slash command invoked by {user_id} with query: {command_text}")
    
    user_profile = next((p for p in matcher.profiles if p["id"] == user_id), None)
    if not user_profile:
        user_profile = {
            "id": user_id,
            "name": f"<@{user_id}>",
            "skills": ["computer science", "python"],
            "location": "Andhra Pradesh",
            "interests": ["scholarships"],
            "slack_channel": channel_id
        }
        
    query = command_text if command_text else "scholarship job training"
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"🔍 Performing real-time scan for *'{query}'*..."
    )
    
    opportunities = search_client.fetch_opportunities(query)
    temp_matcher = OpportunityMatcher(profiles=[user_profile])
    matches = []
    for opp in opportunities:
        matches.extend(temp_matcher.match_opportunity(opp))
        
    if not matches:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="❌ No matching opportunities found for your criteria right now."
        )
        return
        
    for match in matches[:3]:
        payload = SlackMessageGenerator.build_opportunity_block(match)
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=payload["blocks"],
            text=f"New Opportunity: {match['opportunity']['title']}"
        )

# --- Interactive Action Listeners ---

@app.action(re.compile("apply_.*"))
def handle_apply_click(ack, body, logger):
    ack()
    # Simple log of application clicks for metrics
    logger.info(f"User clicked apply button: {body.get('actions', [{}])[0].get('action_id')}")

@app.action(re.compile("calendar_.*"))
def handle_calendar_click(ack, body, client):
    """
    Handles 'Add to Calendar' button. Schedules a simulated calendar reminder
    and notifies the user in a thread.
    """
    ack()
    action = body.get("actions", [{}])[0]
    value_data = json.loads(action.get("value", "{}"))
    title = value_data.get("title", "Opportunity")
    deadline = value_data.get("deadline", "N/A")
    
    channel_id = body.get("channel", {}).get("id")
    message_ts = body.get("message", {}).get("ts")
    user_id = body.get("user", {}).get("id")
    
    # Respond in thread
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=f"📅 <@{user_id}>, I've added a reminder to your calendar for *'{title}'* (Deadline: {deadline}). I will alert you 3 days prior! ⏰"
    )

@app.action(re.compile("share_.*"))
def handle_share_click(ack, body, client):
    """
    Handles 'Share with Team' button. Offers a quick way to share this match
    to a team channel.
    """
    ack()
    action = body.get("actions", [{}])[0]
    value_data = json.loads(action.get("value", "{}"))
    title = value_data.get("title", "Opportunity")
    url = value_data.get("url", "#")
    
    channel_id = body.get("channel", {}).get("id")
    message_ts = body.get("message", {}).get("ts")
    user_id = body.get("user", {}).get("id")
    
    # Post a shared confirmation message to the channel
    client.chat_postMessage(
        channel=channel_id,
        text=f"📢 <@{user_id}> shared the opportunity *\"{title}\"* with the team! Link: {url}"
    )

if __name__ == "__main__":
    app_token = os.getenv("SLACK_APP_TOKEN")
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    
    if not app_token or not bot_token or bot_token == "xoxb-mock-token":
        print("[WARNING] SLACK_APP_TOKEN and SLACK_BOT_TOKEN must be configured in .env for Slack Socket Mode.")
        print("Starting in mock-standalone mode (app.py) for local testing...")
        
        # Standalone mock run
        mock_queries = ["scholarships", "python jobs"]
        for q in mock_queries:
            print(f"\n--- Scanning for Query: '{q}' ---")
            opportunities = search_client.fetch_opportunities(q)
            for opp in opportunities:
                matches = matcher.match_opportunity(opp)
                for match in matches:
                    payload = SlackMessageGenerator.build_opportunity_block(match)
                    print(f"\nMatched User: {match['profile']['name']} (Channel: {match['profile']['slack_channel']})")
                    # Use json.dumps with ascii escaping to avoid stdout encoding errors
                    print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print("[INFO] Slack Opportunity Agent is starting in Socket Mode...")
        handler = SocketModeHandler(app, app_token)
        handler.start()
