import os
import time
import logging
from dotenv import load_dotenv
from slack_sdk import WebClient

# Local modules
from search_client import RealTimeSearchClient
from matcher import OpportunityMatcher
from slack_helper import SlackMessageGenerator

# Load configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

PROCESSED_FILE = "processed_opportunities.txt"

def load_processed_ids() -> set:
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Error reading processed file: {e}")
    return set()

def save_processed_id(opp_id: str):
    try:
        with open(PROCESSED_FILE, "a") as f:
            f.write(f"{opp_id}\n")
    except Exception as e:
        logger.error(f"Error writing to processed file: {e}")

def run_scheduler():
    logger.info("Scheduler daemon started.")
    
    # Initialize Slack Web Client using bot token
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        logger.error("SLACK_BOT_TOKEN is not set in environment. Running in dry-run mode.")
        client = None
    else:
        client = WebClient(token=bot_token)
        
    search_client = RealTimeSearchClient()
    matcher = OpportunityMatcher()
    
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    logger.info(f"Polling interval set to {poll_interval} seconds.")
    
    while True:
        try:
            logger.info("Starting new opportunity scan...")
            processed_ids = load_processed_ids()
            
            # Query the search engine for general queries
            queries = ["scholarships", "jobs", "training programs", "internships"]
            
            for query in queries:
                logger.info(f"Querying search API for '{query}'...")
                opportunities = search_client.fetch_opportunities(query)
                
                for opp in opportunities:
                    opp_id = opp.get("id")
                    
                    # Skip if already processed
                    if opp_id in processed_ids:
                        continue
                        
                    # Match opportunity against beneficiary profiles
                    matches = matcher.match_opportunity(opp)
                    
                    for match in matches:
                        profile = match["profile"]
                        channel = profile.get("slack_channel", "#general")
                        
                        logger.info(f"Found match! Opportunity '{opp.get('title')}' for user '{profile.get('name')}'")
                        
                        # Build message block
                        payload = SlackMessageGenerator.build_opportunity_block(match)
                        
                        if client:
                            try:
                                # Post message to the channel or DM
                                client.chat_postMessage(
                                    channel=channel,
                                    blocks=payload["blocks"],
                                    text=f"New Opportunity Matched: {opp.get('title')}"
                                )
                                logger.info(f"Successfully posted alert to Slack channel {channel}")
                            except Exception as slack_err:
                                logger.error(f"Slack API error posting match: {slack_err}")
                        else:
                            logger.info(f"[DRY-RUN] Would post to {channel}: {opp.get('title')}")
                            
                    # Mark as processed so we don't notify again
                    save_processed_id(opp_id)
                    processed_ids.add(opp_id)
                    
            logger.info("Scan cycle completed. Sleeping...")
            
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            
        time.sleep(poll_interval)

if __name__ == "__main__":
    run_scheduler()
