import gradio as gr
import plotly.graph_objects as go
import pandas as pd
import re
import asyncio
import subprocess
import sys
from datetime import datetime
from bs4 import BeautifulSoup

# ── DO NOT use nest_asyncio — incompatible with Python 3.13 + uvicorn ─────────
# Instead we run the async fetch in a dedicated fresh thread with its own loop.
import threading

PAGE = 'https://result.election.gov.np/PRVoteChartResult2082.aspx'
TOTAL_PR_SEATS = 110

PARTY_COLORS = [
    ('#1565C0', ['स्वतन्त्र']),
    ('#C62828', ['काँग्रेस']),
    ('#E65100', ['मार्क्सवादी', 'एमाले']),
    ('#2E7D32', ['कम्युनिष्ट', 'माओवादी']),
    ('#6A1B9A', ['प्रजातन्त्र']),
    ('#00838F', ['श्रम']),
    ('#F9A825', ['समाजवादी']),
    ('#37474F', ['लोकतान्त्रिक']),
    ('#AD1457', ['जनमोर्चा']),
    ('#4527A0', ['राप्रपा']),
]
EXTRA_COLORS = ['#546E7A','#795548','#5D4037','#607D8B','#78909C','#8D6E63','#A1887F']

# ── Install Playwright browser once ───────────────────────────────────────────
def ensure_browser():
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium', '--with-deps'],
            capture_output=True, text=True, timeout=300
        )
        if r.returncode == 0:
            print('✅ Playwright Chromium ready.')
        else:
            print(f'Browser install warning: {r.stderr[:300]}')
    except Exception as e:
        print(f'Browser install warning: {e}')

ensure_browser()

# ── Helpers ───────────────────────────────────────────────────────────────────
def nep_to_int(s):
    nep = str.maketrans('०१२३४५६७८९', '0123456789')
    cleaned = re.sub(r'[^0-9]', '', s.translate(nep))
    return int(cleaned) if cleaned else 0

def assign_color(name, used):
    for color, kws in PARTY_COLORS:
        if any(k in name for k in kws):
            return color
    for c in EXTRA_COLORS:
        if c not in used:
            return c
    return '#9E9E9E'

# ── Async fetch — runs in its own thread with a clean event loop ───────────────
async def _fetch():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        context = await browser.new_context(user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ))
        page = await context.new_page()
        await page.goto(PAGE, wait_until='networkidle', timeout=60000)
        await page.wait_for_selector('.chart-result-row', timeout=30000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        await browser.close()

    soup  = BeautifulSoup(html, 'html.parser')
    rows  = soup.select('.chart-result-row')
    parties, votes = [], []
    for row in rows:
        n = row.select_one('.result-label')
        c = row.select_one('.prog-count')
        if n and c:
            raw = c.get_text(strip=True)
            v   = nep_to_int(raw)
            if v > 0:
                parties.append(n.get_text(strip=True))
                votes.append(v)
    if not parties:
        raise RuntimeError('No data found — page structure may have changed.')
    return parties, votes

def fetch_live():
    """Run async fetch in a brand-new thread + event loop — safe on all Python versions."""
    result = {}
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result['data'] = loop.run_until_complete(_fetch())
        except Exception as e:
            result['error'] = e
        finally:
            loop.close()
    t = threading.Thread(target=runner)
    t.start()
    t.join()
    if 'error' in result:
        raise result['error']
    return result['data']

# ── Seat allocation ───────────────────────────────────────────────────────────
def allocate_seats(df, total_seats=110):
    """Largest Remainder (Hamilton) method. Only parties >= 3% qualify."""
    eligible = df[df['Percentage'] >= 3.0].copy()
    quota = total_seats / eligible['Votes'].sum()
    eligible['ExactSeats'] = eligible['Votes'] * quota
    eligible['BaseSeats']  = eligible['ExactSeats'].apply(int)
    eligible['Remainder']  = eligible['ExactSeats'] - eligible['BaseSeats']
    remaining = total_seats - eligible['BaseSeats'].sum()
    top_idx = eligible['Remainder'].nlargest(int(remaining)).index
    eligible.loc[top_idx, 'BaseSeats'] += 1
    eligible['Seats'] = eligible['BaseSeats'].astype(int)
    return eligible[['Party','Votes','Percentage','Color','Seats']].reset_index(drop=True)

# ── Chart builders ────────────────────────────────────────────────────────────
def build_charts(parties, votes):
    used, colors = [], []
    for p in parties:
        c = assign_color(p, used)
        colors.append(c); used.append(c)

    df = pd.DataFrame({'Party': parties, 'Votes': votes, 'Color': colors})
    total_votes = df['Votes'].sum()
    df['Percentage'] = (df['Votes'] / total_votes * 100).round(2)
    df = df.sort_values('Votes', ascending=False).reset_index(drop=True)
    timestamp = datetime.now().strftime('%d %b %Y, %H:%M NPT')

    # Chart 1 — vote share, Others grouping
    major  = df[df['Percentage'] >= 3.0].copy()
    others = df[df['Percentage'] <  3.0]
    if not others.empty:
        chart1_df = pd.concat([major, pd.DataFrame([{
            'Party': 'Others (< 3%)', 'Votes': others['Votes'].sum(),
            'Color': '#9E9E9E', 'Percentage': round(others['Percentage'].sum(), 2)
        }])], ignore_index=True)
    else:
        chart1_df = major.copy()
    chart1_df = chart1_df.sort_values('Votes', ascending=False).reset_index(drop=True)

    hover1 = [f"<b>{r['Party']}</b><br>Votes: {r['Votes']:,}<br>Share: {r['Percentage']:.2f}%"
              for _, r in chart1_df.iterrows()]

    fig1 = go.Figure(go.Pie(
        labels=chart1_df['Party'], values=chart1_df['Votes'], hole=0.42,
        hovertemplate="%{customdata}<extra></extra>", customdata=hover1,
        texttemplate="<b>%{percent:.1%}</b>", textposition='inside',
        insidetextorientation='radial',
        marker=dict(colors=chart1_df['Color'].tolist(), line=dict(color='white', width=2.5)),
        pull=[0.07 if i==0 else 0 for i in range(len(chart1_df))],
        sort=False, direction='clockwise', rotation=90,
    ))
    fig1.update_layout(
        title=dict(
            text=(f"<b>Chart 1 — PR Vote Share</b><br>"
                  f"<sup>जम्मा मत: {total_votes:,} &nbsp;|&nbsp; 🔴 LIVE &nbsp;|&nbsp; {timestamp}</sup>"),
            x=0.5, xanchor='center', font=dict(size=15, family='Georgia')),
        annotations=[dict(text=f"जम्मा मत<br><b>{total_votes/1e6:.2f}M</b>",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=13, color='#222', family='Georgia'))],
        legend=dict(orientation='v', x=1.01, y=0.5, font=dict(size=11),
                    bgcolor='rgba(255,255,255,0.9)', bordercolor='#ddd', borderwidth=1),
        margin=dict(t=110, b=50, l=30, r=230),
        height=580, paper_bgcolor='#FAFAFA',
    )

    # Chart 2 — 110 seats, no Others
    seats_df = allocate_seats(df, TOTAL_PR_SEATS)
    seats_df = seats_df.sort_values('Seats', ascending=False).reset_index(drop=True)

    hover2 = [f"<b>{r['Party']}</b><br>Seats: {r['Seats']}<br>Vote share: {r['Percentage']:.2f}%"
              for _, r in seats_df.iterrows()]

    fig2 = go.Figure(go.Pie(
        labels=seats_df['Party'], values=seats_df['Seats'], hole=0.42,
        hovertemplate="%{customdata}<extra></extra>", customdata=hover2,
        texttemplate="<b>%{label}</b><br>%{value} seats", textposition='outside',
        marker=dict(colors=seats_df['Color'].tolist(), line=dict(color='white', width=2.5)),
        pull=[0.07 if i==0 else 0 for i in range(len(seats_df))],
        sort=False, direction='clockwise', rotation=90,
    ))
    fig2.update_layout(
        title=dict(
            text=(f"<b>Chart 2 — 110 PR Seat Allocation</b><br>"
                  f"<sup>Parties ≥ 3% · Largest Remainder method · {timestamp}</sup>"),
            x=0.5, xanchor='center', font=dict(size=15, family='Georgia')),
        annotations=[dict(text=f"<b>{TOTAL_PR_SEATS}</b><br>PR Seats",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#222', family='Georgia'))],
        legend=dict(orientation='v', x=1.01, y=0.5, font=dict(size=11),
                    bgcolor='rgba(255,255,255,0.9)', bordercolor='#ddd', borderwidth=1),
        margin=dict(t=110, b=80, l=30, r=230),
        height=600, paper_bgcolor='#FAFAFA',
    )

    # Summary table
    summary = seats_df[['Party','Votes','Percentage','Seats']].copy()
    summary.columns = ['Party','Votes','Vote %','PR Seats (110)']
    summary['Votes']  = summary['Votes'].apply(lambda x: f'{x:,}')
    summary['Vote %'] = summary['Vote %'].apply(lambda x: f'{x:.2f}%')

    return fig1, fig2, summary, timestamp, total_votes

# ── Gradio callback ───────────────────────────────────────────────────────────
def refresh_data():
    try:
        parties, votes = fetch_live()
        fig1, fig2, summary, ts, total = build_charts(parties, votes)
        status = f"✅ Live data fetched at {ts} — {len(parties)} parties, {total:,} total votes"
        return fig1, fig2, summary, status
    except Exception as e:
        msg = f"❌ Error: {e}"
        empty = go.Figure()
        empty.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False,
                             font=dict(size=13, color='red'))
        empty.update_layout(paper_bgcolor='#FAFAFA')
        return empty, empty, pd.DataFrame(), msg

# ── Gradio UI ─────────────────────────────────────────────────────────────────
CSS = """
body { font-family: Georgia, serif !important; background: #F0F2F5; }
.gradio-container { max-width: 1100px !important; margin: 0 auto !important; }
#title    { text-align:center; color:#1a237e; font-size:1.5rem; font-weight:bold; margin-bottom:2px; }
#subtitle { text-align:center; color:#555; font-size:0.88rem; margin-bottom:10px; }
#disclaimer {
    background: #FFF8E1;
    border-left: 5px solid #F9A825;
    border-radius: 6px;
    padding: 12px 18px;
    margin: 10px 0 16px 0;
    font-size: 0.86rem;
    color: #5D4037;
    line-height: 1.6;
}
#disclaimer strong { color: #E65100; }
#disclaimer a { color: #1565C0; font-weight: bold; }
#status textarea { background:#E8F5E9 !important; color:#1B5E20 !important;
                   border-left:4px solid #2E7D32 !important; font-size:0.85rem !important; }
#footer { text-align:center; color:#aaa; font-size:0.75rem; margin-top:14px; }
"""

with gr.Blocks(title="Nepal Election 2082 — PR Results") as demo:
    gr.HTML("""
        <div id='title'>🗳️ Nepal Election 2082 — Proportional Representation Results</div>
        <div id='subtitle'>
            समानुपातिक निर्वाचनमा मतगणनाको आधारमा दलगत स्थिति &nbsp;|&nbsp;
            Live · <a href='https://result.election.gov.np/PRVoteChartResult2082.aspx'
            target='_blank'>Election Commission of Nepal</a>
        </div>
    """)

    gr.HTML("""
        <div id='disclaimer'>
            ⚠️ <strong>Educational &amp; Learning Purpose Only</strong><br>
            This app is built for <strong>educational purposes only</strong> and is
            <strong>not affiliated</strong> with the Election Commission of Nepal or
            any political party. Data is fetched automatically from the EC website and
            may be delayed or incomplete due to scraping limitations.<br><br>
            👉 For <strong>official and accurate election results</strong>, always use the
            authoritative source:
            <a href='https://result.election.gov.np/PRVoteChartResult2082.aspx'
               target='_blank'>
               Election Commission of Nepal — result.election.gov.np
            </a>
        </div>
    """)

    status_box = gr.Textbox(elem_id="status", interactive=False,
                            show_label=False, container=False)
    refresh_btn = gr.Button("🔄 Refresh Live Data", variant="primary", size="lg")

    with gr.Tabs():
        with gr.Tab("📊 Chart 1 — Vote Share"):
            chart1_out = gr.Plot(show_label=False)
            gr.HTML("<p style='text-align:center;color:#888;font-size:0.8rem'>"
                    "Parties &lt; 3% grouped as <b>Others</b></p>")
        with gr.Tab("🏛️ Chart 2 — 110 Seat Allocation"):
            chart2_out = gr.Plot(show_label=False)
            gr.HTML("<p style='text-align:center;color:#888;font-size:0.8rem'>"
                    "Only parties ≥ 3% · <b>Largest Remainder</b> method · no Others group</p>")
        with gr.Tab("📋 Seat Summary Table"):
            table_out = gr.DataFrame(
                headers=['Party','Votes','Vote %','PR Seats (110)'],
                interactive=False)

    refresh_btn.click(fn=refresh_data,
                      outputs=[chart1_out, chart2_out, table_out, status_box])

    gr.HTML("""
        <div id='footer'>
            Data: result.election.gov.np &nbsp;·&nbsp;
            Counting ongoing — click Refresh for latest &nbsp;·&nbsp;
            Nepal HoR Election 2082 (2026) &nbsp;·&nbsp; MIT License
        </div>
    """)

    demo.load(fn=refresh_data, outputs=[chart1_out, chart2_out, table_out, status_box])

if __name__ == '__main__':
    demo.launch(css=CSS)