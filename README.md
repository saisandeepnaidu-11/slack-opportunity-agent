# Slack Agent for Good – Real-Time Opportunity Finder

This Slack agent integrates Slack capabilities (using interactive Block Kit messages) with real-time opportunity ingestion to alert team members/channels when scholarships, job openings, training programs, or community initiatives matching their profiles are found.

## Features
- **Real-Time Search Ingestion**: Simulates or queries search engines/APIs for newly posted opportunities (scholarships, job openings, etc.).
- **User Profile Matching**: Matches opportunity tags (skills, location, topics) with team member profiles.
- **Smart Slack Notifications**: Formats matches as rich Block Kit messages with:
  - Concise summaries
  - Dynamic buttons to schedule reminders ("Add to Calendar") or share with specific channels ("Share with Team").
- **Interactive Handlers**: Handles Slack button clicks and interactive commands in real-time.

## Installation & Setup

1. **Clone/Navigate to this folder**:
   ```bash
   cd "d:\RAG PROJECT\slack_opportunity_agent"
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your Slack application credentials.
   ```bash
   copy .env.example .env
   ```

4. **Run the Slack App**:
   By default, the app runs in **Socket Mode** so you don't need a public HTTPS endpoint for development.
   ```bash
   python app.py
   ```

5. **Run the Daemon Scheduler**:
   To poll for opportunities in the background:
   ```bash
   python scheduler.py
   ```
