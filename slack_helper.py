import json
from typing import Dict, Any

class SlackMessageGenerator:
    """
    Constructs highly engaging, premium Slack Block Kit messages for opportunities.
    """
    
    @staticmethod
    def get_type_emoji(opp_type: str) -> str:
        mapping = {
            "scholarship": "🎓",
            "job": "💼",
            "training": "🛠️",
            "internship": "🌱",
            "fellowship": "🌟"
        }
        return mapping.get(opp_type.lower(), "📢")

    @staticmethod
    def generate_personalized_summary(opportunity: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """
        Simulates Slack AI or LLM personalization to tailor the summary for the user.
        """
        opp_title = opportunity.get("title")
        opp_org = opportunity.get("organization")
        opp_desc = opportunity.get("description")
        user_name = profile.get("name")
        user_skills = profile.get("skills", [])
        
        # Simple rule-based personalized AI summarizer representing what a Slack AI query returns
        matched_user_skills = [s for s in user_skills if s.lower() in opp_desc.lower() or s.lower() in opp_title.lower()]
        
        summary = (
            f"Hey *{user_name}*! 👋 Here is an opportunity that matches your profile:\n\n"
            f"*Summary:* {opp_desc}\n"
        )
        
        if matched_user_skills:
            skills_str = ", ".join([f"`{s}`" for s in matched_user_skills])
            summary += f"💡 *Why it matches you:* It aligns directly with your skills in {skills_str}.\n"
        else:
            summary += f"💡 *Why it matches you:* Matches your interest in *{opportunity.get('type')}s* in *{profile.get('location')}*.\n"
            
        return summary

    @classmethod
    def build_opportunity_block(cls, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a Slack Block Kit payload for a matched opportunity.
        """
        profile = match_data["profile"]
        opportunity = match_data["opportunity"]
        reasons = match_data["reasons"]
        
        opp_id = opportunity.get("id")
        opp_type = opportunity.get("type", "Opportunity")
        title = opportunity.get("title")
        org = opportunity.get("organization")
        deadline = opportunity.get("deadline")
        url = opportunity.get("url")
        loc = opportunity.get("location")
        
        emoji = cls.get_type_emoji(opp_type)
        ai_summary = cls.generate_personalized_summary(opportunity, profile)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *New Opportunity Matched: {title}*"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ai_summary
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🏢 *Organization:* {org}  |  📍 *Location:* {loc}  |  📅 *Deadline:* {deadline}"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": f"actions_{opp_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔗 View & Apply",
                            "emoji": True
                        },
                        "url": url,
                        "action_id": f"apply_{opp_id}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📅 Add to Calendar",
                            "emoji": True
                        },
                        "value": json.dumps({"title": title, "deadline": deadline}),
                        "action_id": f"calendar_{opp_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📢 Share with Team",
                            "emoji": True
                        },
                        "value": json.dumps({"title": title, "url": url}),
                        "action_id": f"share_{opp_id}"
                    }
                ]
            }
        ]
        
        return {"blocks": blocks}
