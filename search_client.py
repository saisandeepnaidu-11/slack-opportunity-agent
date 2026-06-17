import os
import requests
from typing import List, Dict, Any
from datetime import datetime

class RealTimeSearchClient:
    """
    Client to fetch real-time opportunity updates from job boards, 
    scholarships, training programs, and local government initiatives.
    """
    def __init__(self, api_key: str = None, cx: str = None):
        self.api_key = api_key or os.getenv("REALTIME_SEARCH_API_KEY")
        self.cx = cx or os.getenv("REALTIME_SEARCH_CX")
        
        # In-memory mock database of recent opportunities to serve as a high-fidelity fallback or primary source
        self.mock_opportunities = [
            {
                "id": "opp_001",
                "title": "Andhra Pradesh Merit Scholarship for Computer Science",
                "type": "Scholarship",
                "description": "Full-tuition scholarship for undergraduate Computer Science students studying in universities within Andhra Pradesh. Focuses on supporting low-income and underserved student categories.",
                "organization": "AP Government Education Department",
                "location": "Andhra Pradesh",
                "deadline": "2026-07-15",
                "url": "https://education.ap.gov.in/scholarships",
                "tags": ["scholarship", "computer science", "andhra pradesh", "education"],
                "posted_at": "2026-06-15T10:00:00Z"
            },
            {
                "id": "opp_002",
                "title": "Junior Python Developer Program - Diversity & Inclusion",
                "type": "Job",
                "description": "Remote entry-level Python developer job with strong mentorship and training. Specially designed for recent graduates from underrepresented engineering institutions.",
                "organization": "TechForward Foundation",
                "location": "Remote",
                "deadline": "2026-06-30",
                "url": "https://techforward.org/careers",
                "tags": ["job", "python", "developer", "software engineering", "remote"],
                "posted_at": "2026-06-16T08:30:00Z"
            },
            {
                "id": "opp_003",
                "title": "Data Analytics Bootcamp for Women in STEM",
                "type": "Training",
                "description": "A fully-funded 12-week intensive bootcamp covering SQL, Python, and Tableau. Includes placement assistance with partner tech companies.",
                "organization": "WomenInTech India",
                "location": "Hyderabad",
                "deadline": "2026-07-05",
                "url": "https://womenintech.in/bootcamp",
                "tags": ["training", "data analytics", "python", "sql", "hyderabad", "women in stem"],
                "posted_at": "2026-06-16T12:00:00Z"
            },
            {
                "id": "opp_004",
                "title": "Rural Tech Fellowship 2026",
                "type": "Internship",
                "description": "6-month paid internship opportunity for young professionals to work on digital literacy and tech deployments in rural schools of Andhra Pradesh and Telangana.",
                "organization": "Digital India Trust",
                "location": "Telangana",
                "deadline": "2026-07-20",
                "url": "https://digitalindiatrust.org/fellowship",
                "tags": ["internship", "social work", "education", "telangana", "andhra pradesh"],
                "posted_at": "2026-06-14T09:00:00Z"
            }
        ]

    def fetch_opportunities(self, query: str = "scholarships jobs initiatives") -> List[Dict[str, Any]]:
        """
        Fetches opportunities. If API credentials are set, queries the Google Custom Search API.
        Otherwise, filters the mock opportunity database to provide local/reproducible behavior.
        """
        if self.api_key and self.cx:
            return self._fetch_from_google_search(query)
        else:
            return self._fetch_from_mock(query)

    def _fetch_from_mock(self, query: str) -> List[Dict[str, Any]]:
        # Return all opportunities scored by relevance — the matcher handles filtering
        query_words = query.lower().split()
        scored = []
        for opp in self.mock_opportunities:
            match_score = 0
            text_to_search = (
                opp["title"] + " " + 
                opp["description"] + " " + 
                opp["location"] + " " + 
                " ".join(opp["tags"])
            ).lower()
            text_words = text_to_search.split()

            for word in query_words:
                if word in text_to_search:
                    match_score += 2
                elif any(
                    word.startswith(t[:max(4, len(t)-1)]) or
                    t.startswith(word[:max(4, len(word)-1)])
                    for t in text_words if len(t) >= 4
                ):
                    match_score += 1
            
            scored.append((match_score, opp))
        
        # Sort by relevance score descending, then by posted_at
        scored.sort(key=lambda x: (x[0], x[1].get("posted_at", "")), reverse=True)
        return [opp for _, opp in scored]

    def _fetch_from_google_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Real integration with Google Custom Search API to find real-time links.
        This parses search results and wraps them in our opportunity structure.
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 5
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            opportunities = []
            for index, item in enumerate(data.get("items", [])):
                # Map Google search result to opportunity schema
                opp = {
                    "id": f"search_{index}_{datetime.now().strftime('%s')}" if hasattr(datetime.now(), 'strftime') else f"search_{index}",
                    "title": item.get("title", ""),
                    "type": "External Search Match",
                    "description": item.get("snippet", ""),
                    "organization": item.get("displayLink", "Web Search Source"),
                    "location": "Various / Online",
                    "deadline": "Check website for details",
                    "url": item.get("link", ""),
                    "tags": [word.lower() for word in query.split() if len(word) > 3],
                    "posted_at": datetime.now().isoformat() + "Z"
                }
                opportunities.append(opp)
            return opportunities
        except Exception as e:
            print(f"Error fetching from Google Custom Search API: {e}")
            # Fallback to mock data on error so execution doesn't crash
            return self._fetch_from_mock(query)
