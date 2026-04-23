# Experiment #002 — Morning Brief

An automated daily morning brief covering markets, news, and sports. Pulls live data, generates an AI summary via Claude API, outputs a formatted HTML page published to the site.

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python brief.py`

Output is written to `output/latest.html`.
