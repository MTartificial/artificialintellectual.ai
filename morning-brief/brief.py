# Orchestrates the morning brief: fetches market + news data, generates AI summary via Claude, outputs HTML

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

from sources.markets import get_market_data
from sources.news import get_headlines

load_dotenv()

WATCHLIST = ["MU", "AMD", "NVDA", "QCOM", "MSFT"]
NEWS_CATEGORIES = ["technology", "business", "general"]
OUTPUT_PATH = Path(__file__).parent / "output" / "latest.html"


def build_prompt(market_data: dict, news_data: dict) -> str:
    lines = ["You are writing a concise morning brief for a retail investor focused on semiconductors."]
    lines.append("")

    lines.append("## MARKET DATA (today's moves)")
    for symbol, d in market_data.items():
        if "error" in d:
            lines.append(f"  {symbol}: ERROR — {d['error']}")
        else:
            sign = "+" if d["change_dollar"] >= 0 else ""
            lines.append(
                f"  {symbol}: ${d['price']:.2f}  {sign}{d['change_dollar']:.2f} ({sign}{d['change_pct']:.2f}%)"
            )

    lines.append("")
    lines.append("## NEWS HEADLINES")
    for category, articles in news_data.items():
        lines.append(f"\n  [{category.upper()}]")
        if isinstance(articles, dict) and "error" in articles:
            lines.append(f"    ERROR: {articles['error']}")
        else:
            for a in articles:
                lines.append(f"    - {a['title']} ({a['source']})")

    lines.append("")
    lines.append("""Write a morning brief with exactly two sections:

**MARKETS**
Summarize the watchlist moves. Note anything significant — big moves, divergences, sector themes. Add brief context where relevant (macro, earnings, sentiment). Keep it tight, 3-5 sentences.

**NEWS**
Pick the 3-4 most interesting or market-relevant headlines across all categories. One sentence of commentary per headline — what it means, why it matters, or what to watch.

Tone: direct, intelligent, no fluff. Write like a smart friend who follows markets, not a financial advisor. No disclaimers.""")

    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found — check your .env file")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def render_html(brief_text: str, market_data: dict, generated_at: datetime) -> str:
    date_str = generated_at.strftime("%A, %B %d, %Y").replace(" 0", " ")
    time_str = generated_at.strftime("%I:%M %p").lstrip("0")

    # Build market ticker rows
    ticker_rows = []
    for symbol, d in market_data.items():
        if "error" in d:
            ticker_rows.append(f"""
        <div class="ticker-item">
          <span class="ticker-symbol">{symbol}</span>
          <span class="ticker-price" style="font-size:1rem; color:var(--muted);">ERR</span>
        </div>""")
        else:
            color = "#4caf50" if d["change_dollar"] >= 0 else "#ef5350"
            sign = "+" if d["change_dollar"] >= 0 else ""
            ticker_rows.append(f"""
        <div class="ticker-item">
          <span class="ticker-symbol">{symbol}</span>
          <span class="ticker-price">${d['price']:.2f}</span>
          <span class="ticker-change" style="color:{color}; opacity:1;">{sign}{d['change_dollar']:.2f} ({sign}{d['change_pct']:.2f}%)</span>
        </div>""")

    # Convert brief_text markdown-ish formatting to HTML
    html_brief = ""
    for line in brief_text.strip().split("\n"):
        stripped = line.strip()
        if stripped.startswith("**") and stripped.endswith("**"):
            heading = stripped.strip("*")
            html_brief += f'<h3 class="brief-section-heading">{heading}</h3>\n'
        elif stripped == "":
            html_brief += "<br>\n"
        else:
            html_brief += f"<p>{stripped}</p>\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Morning Brief — {date_str}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:        #0d0d0f;
      --bg-card:   #141417;
      --bg-hover:  #1a1a1f;
      --border:    #222228;
      --text:      #e2e2e8;
      --muted:     #7a7a88;
      --accent:    #7c6fff;
      --accent2:   #4fc3f7;
      --tag-bg:    #1e1e26;
      --font:      'Georgia', 'Times New Roman', serif;
      --mono:      'Courier New', Courier, monospace;
    }}

    html {{ scroll-behavior: smooth; font-size: 16px; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      line-height: 1.7;
      min-height: 100vh;
    }}

    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg); }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

    nav {{
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 2rem;
      height: 58px;
      background: rgba(13, 13, 15, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }}

    .nav-brand {{
      font-family: var(--mono);
      font-size: 0.82rem;
      letter-spacing: 0.04em;
      color: var(--muted);
      text-decoration: none;
    }}
    .nav-brand span {{ color: var(--accent); }}

    .nav-meta {{
      font-family: var(--mono);
      font-size: 0.72rem;
      color: var(--muted);
      opacity: 0.5;
    }}

    .container {{
      max-width: 860px;
      margin: 0 auto;
      padding: 0 1.5rem;
    }}

    .page-header {{
      padding: 7rem 0 3rem;
    }}

    .page-label {{
      font-family: var(--mono);
      font-size: 0.7rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 0.6rem;
      display: block;
    }}

    .page-title {{
      font-size: clamp(1.8rem, 4vw, 2.8rem);
      font-weight: normal;
      letter-spacing: -0.02em;
      line-height: 1.1;
      color: #ebebf3;
      margin-bottom: 0.5rem;
    }}

    .page-date {{
      font-family: var(--mono);
      font-size: 0.8rem;
      color: var(--muted);
      opacity: 0.6;
    }}

    .section-divider {{
      width: 100%;
      height: 1px;
      background: var(--border);
      margin: 2.5rem 0;
    }}

    /* Market ticker strip */
    .market-strip {{
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 2.5rem;
    }}

    .market-strip-header {{
      padding: 0.75rem 1.5rem;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .market-strip-title {{
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    .market-strip-time {{
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--muted);
      opacity: 0.45;
    }}

    .market-strip-body {{
      padding: 1.5rem;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 1.25rem;
      background: var(--bg-card);
    }}

    .ticker-item {{ display: flex; flex-direction: column; gap: 0.2rem; }}

    .ticker-symbol {{
      font-family: var(--mono);
      font-size: 0.75rem;
      letter-spacing: 0.1em;
      color: var(--muted);
    }}

    .ticker-price {{
      font-size: 1.3rem;
      letter-spacing: -0.02em;
      color: var(--text);
    }}

    .ticker-change {{
      font-family: var(--mono);
      font-size: 0.7rem;
    }}

    /* Brief body */
    .brief-body {{
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 3rem;
    }}

    .brief-body-inner {{
      padding: 2rem 2.5rem;
      background: var(--bg-card);
    }}

    .brief-section-heading {{
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--accent);
      margin: 1.75rem 0 0.75rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }}

    .brief-section-heading:first-child {{ margin-top: 0; }}

    .brief-body-inner p {{
      font-size: 0.975rem;
      color: #c8c8d4;
      line-height: 1.85;
      margin-bottom: 0.6rem;
    }}

    .brief-footer {{
      padding: 0.85rem 1.5rem;
      background: var(--bg);
      border-top: 1px solid var(--border);
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--muted);
      opacity: 0.4;
    }}

    footer {{
      border-top: 1px solid var(--border);
      padding: 2rem 1.5rem;
      margin-top: 4rem;
    }}

    .footer-inner {{
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .footer-brand {{
      font-family: var(--mono);
      font-size: 0.75rem;
      color: var(--muted);
      opacity: 0.5;
      letter-spacing: 0.04em;
    }}

    .footer-note {{
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--muted);
      opacity: 0.35;
      font-style: italic;
    }}

    @media (max-width: 640px) {{
      .market-strip-body {{ grid-template-columns: 1fr 1fr; }}
      .brief-body-inner {{ padding: 1.5rem; }}
    }}
  </style>
</head>
<body>

  <nav>
    <a href="../index.html" class="nav-brand"><span>ai</span>·intellectual</a>
    <span class="nav-meta">morning brief</span>
  </nav>

  <div class="container">
    <div class="page-header">
      <span class="page-label">Experiment #002 — Morning Brief</span>
      <h1 class="page-title">{date_str}</h1>
      <span class="page-date">Generated at {time_str} · Claude Sonnet 4.6 · yfinance + NewsAPI</span>
    </div>

    <div class="section-divider"></div>

    <div class="market-strip">
      <div class="market-strip-header">
        <span class="market-strip-title">Watchlist</span>
        <span class="market-strip-time">Pulled at {time_str}</span>
      </div>
      <div class="market-strip-body">
        {"".join(ticker_rows)}
      </div>
    </div>

    <div class="brief-body">
      <div class="brief-body-inner">
        {html_brief}
      </div>
      <div class="brief-footer">AI-generated summary · Not financial advice · Data via yfinance and NewsAPI</div>
    </div>
  </div>

  <footer>
    <div class="container footer-inner">
      <span class="footer-brand">artificialintellectual.ai</span>
      <span class="footer-note">Built with Claude Code · Updated daily</span>
    </div>
  </footer>

</body>
</html>"""


def main():
    print("Fetching market data...")
    market_data = get_market_data(WATCHLIST)

    print("Fetching news headlines...")
    news_data = get_headlines(NEWS_CATEGORIES)

    print("Calling Claude...")
    prompt = build_prompt(market_data, news_data)
    brief_text = call_claude(prompt)

    print("Writing HTML...")
    generated_at = datetime.now()
    html = render_html(brief_text, market_data, generated_at)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    print("Brief generated successfully →", OUTPUT_PATH)


if __name__ == "__main__":
    main()
