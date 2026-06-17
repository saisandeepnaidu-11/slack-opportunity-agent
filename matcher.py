import re
from typing import List, Dict, Any

class OpportunityMatcher:
    """
    Profile Matching Engine. 
    Matches ingested opportunities against user profiles based on skills, location, and interests.
    """
    def __init__(self, profiles: List[Dict[str, Any]] = None):
        # Default mock profiles representing beneficiary lists or team members
        self.profiles = profiles or [
            {
                "id": "U12345678A",  # Example Slack User ID
                "name": "Sandeep Naidu",
                "email": "sandeep@example.org",
                "skills": ["python", "computer science", "software engineering", "ml"],
                "location": "Andhra Pradesh",
                "interests": ["scholarship", "internship", "fellowship"],
                "slack_channel": "@sandeep" # Direct message or personal notify channel
            },
            {
                "id": "U12345678B",
                "name": "Priya Sharma",
                "email": "priya@example.org",
                "skills": ["sql", "tableau", "data analytics", "python"],
                "location": "Hyderabad",
                "interests": ["training", "bootcamp", "job"],
                "slack_channel": "#data-opportunities"
            },
            {
                "id": "U12345678C",
                "name": "Anjali Kumar",
                "email": "anjali@example.org",
                "skills": ["education", "literacy", "teaching", "social work"],
                "location": "Telangana",
                "interests": ["fellowship", "internship", "volunteer"],
                "slack_channel": "#community-programs"
            }
        ]

    def match_opportunity(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Computes match score for an opportunity across all user/beneficiary profiles.
        Returns a list of matched records with score > 0, sorted by score descending.
        """
        matched_results = []
        
        opp_title = opportunity.get("title", "").lower()
        opp_desc = opportunity.get("description", "").lower()
        opp_loc = opportunity.get("location", "").lower()
        opp_tags = [t.lower() for t in opportunity.get("tags", [])]
        
        full_text = f"{opp_title} {opp_desc} {' '.join(opp_tags)}"
        
        for profile in self.profiles:
            score = 0
            matching_reasons = []
            
            # 1. Location Matching
            prof_loc = profile.get("location", "").lower()
            if prof_loc and (prof_loc in opp_loc or prof_loc in full_text):
                score += 5  # High priority for location match
                matching_reasons.append(f"Location match: {profile.get('location')}")
            elif opp_loc == "remote" or "remote" in full_text:
                score += 2
                matching_reasons.append("Remote opportunity")
                
            # 2. Skills Matching
            matched_skills = []
            for skill in profile.get("skills", []):
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, full_text):
                    score += 3
                    matched_skills.append(skill)
            
            if matched_skills:
                matching_reasons.append(f"Matching skills: {', '.join(matched_skills)}")
                
            # 3. Interests Matching (e.g. Scholarship, Job)
            matched_interests = []
            for interest in profile.get("interests", []):
                pattern = r'\b' + re.escape(interest.lower()) + r'\b'
                if re.search(pattern, full_text):
                    score += 2
                    matched_interests.append(interest)
            
            if matched_interests:
                matching_reasons.append(f"Matching interests: {', '.join(matched_interests)}")
                
            # If there's some baseline skill/interest match, include in result
            if score >= 3:
                matched_results.append({
                    "profile": profile,
                    "opportunity": opportunity,
                    "score": score,
                    "reasons": matching_reasons
                })
                
        # Sort matches by score descending
        matched_results.sort(key=lambda x: x["score"], reverse=True)
        return matched_results
