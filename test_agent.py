import pytest
from search_client import RealTimeSearchClient
from matcher import OpportunityMatcher
from slack_helper import SlackMessageGenerator

def test_search_client_fallback():
    client = RealTimeSearchClient()
    # Query matching AP Government Merit Scholarship
    results = client.fetch_opportunities("Andhra Pradesh")
    assert len(results) >= 1
    titles = [opp["title"] for opp in results]
    assert any("Andhra Pradesh Merit Scholarship" in title for title in titles)

def test_opportunity_matcher_ap_scholarship():
    matcher = OpportunityMatcher()
    
    # Andhra Pradesh scholarship opportunity
    ap_scholarship = {
        "id": "opp_001",
        "title": "Andhra Pradesh Merit Scholarship for Computer Science",
        "type": "Scholarship",
        "description": "Full-tuition scholarship for undergraduate Computer Science students studying in universities within Andhra Pradesh.",
        "organization": "AP Government Education Department",
        "location": "Andhra Pradesh",
        "deadline": "2026-07-15",
        "url": "https://education.ap.gov.in/scholarships",
        "tags": ["scholarship", "computer science", "andhra pradesh"],
        "posted_at": "2026-06-15T10:00:00Z"
    }
    
    matches = matcher.match_opportunity(ap_scholarship)
    
    # Should match Sandeep Naidu (Andhra Pradesh, computer science, scholarship)
    assert len(matches) > 0
    best_match = matches[0]
    assert best_match["profile"]["name"] == "Sandeep Naidu"
    assert any("Location match" in reason for reason in best_match["reasons"])
    assert any("Matching skills" in reason for reason in best_match["reasons"])

def test_opportunity_matcher_hyderabad_bootcamp():
    matcher = OpportunityMatcher()
    
    # Hyderabad bootcamp
    bootcamp = {
        "id": "opp_003",
        "title": "Data Analytics Bootcamp for Women in STEM",
        "type": "Training",
        "description": "A fully-funded 12-week intensive bootcamp covering SQL, Python, and Tableau.",
        "organization": "WomenInTech India",
        "location": "Hyderabad",
        "deadline": "2026-07-05",
        "url": "https://womenintech.in/bootcamp",
        "tags": ["training", "data analytics", "python", "sql", "hyderabad"],
        "posted_at": "2026-06-16T12:00:00Z"
    }
    
    matches = matcher.match_opportunity(bootcamp)
    
    # Should match Priya Sharma (Hyderabad, sql, python, data analytics)
    assert len(matches) > 0
    best_match = matches[0]
    assert best_match["profile"]["name"] == "Priya Sharma"
    assert any("Location match" in reason for reason in best_match["reasons"])
    assert any("Matching skills" in reason for reason in best_match["reasons"])

def test_slack_message_payload():
    match_data = {
        "profile": {
            "name": "Sandeep Naidu",
            "skills": ["python"],
            "location": "Andhra Pradesh",
            "interests": ["scholarship"],
            "slack_channel": "@sandeep"
        },
        "opportunity": {
            "id": "opp_001",
            "title": "Andhra Pradesh Merit Scholarship",
            "type": "Scholarship",
            "description": "AP Scholarship for CS",
            "organization": "AP Gov",
            "location": "Andhra Pradesh",
            "deadline": "2026-07-15",
            "url": "https://ap.gov",
            "tags": ["scholarship"]
        },
        "reasons": ["Location match: Andhra Pradesh"]
    }
    
    payload = SlackMessageGenerator.build_opportunity_block(match_data)
    
    # Validate block kit format
    assert "blocks" in payload
    assert len(payload["blocks"]) >= 4
    
    # First block should be the section header
    assert payload["blocks"][0]["type"] == "section"
    assert "Andhra Pradesh Merit Scholarship" in payload["blocks"][0]["text"]["text"]
    
    # Actions block should contain three buttons
    actions_block = payload["blocks"][-1]
    assert actions_block["type"] == "actions"
    assert len(actions_block["elements"]) == 3
    
    # Verify button URLs and action ids
    assert actions_block["elements"][0]["url"] == "https://ap.gov"
    assert actions_block["elements"][0]["action_id"] == "apply_opp_001"
