---
title: Nepal Election 2082 PR Results
emoji: 🗳️
colorFrom: blue
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# 🗳️ Nepal Election 2082 — Proportional Representation Results

[![GitHub Repo](https://img.shields.io/badge/GitHub-nepal--election--2082-181717?style=flat&logo=github)](https://github.com/YOUR_USERNAME/nepal-election-2082)
[![Hugging Face Space](https://img.shields.io/badge/🤗%20Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/YOUR_USERNAME/nepal-election-2082)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

> ⚠️ **DISCLAIMER — Educational Purpose Only**
>
> This app is built **for learning and educational purposes only**.
> The data is fetched automatically from the Election Commission of Nepal website
> and may be delayed, incomplete, or inaccurate due to scraping limitations.
>
> **For official and accurate election results, always refer to the
> [Election Commission of Nepal](https://result.election.gov.np/PRVoteChartResult2082.aspx)
> — the only authoritative source.**

---

## 📊 What This App Shows

- **Chart 1 — Vote Share** — Live PR vote share pie chart. Parties with less than 3% of
  the vote are grouped together as *Others*.
- **Chart 2 — 110 Seat Allocation** — Proportional seat allocation across Nepal's 110 PR
  seats. Only parties meeting the 3% threshold qualify. Seats calculated using the
  **Largest Remainder (Hamilton)** method.
- **Table** — Full summary showing each party's votes, vote percentage, and allocated seats.
- **🔄 Refresh button** — Fetches the latest live data from the Election Commission on demand.

---

## 🖥️ Run Locally (Windows / Mac / Linux)

### Prerequisites
- Python 3.10, 3.11, or 3.12 recommended (Python 3.13 supported)
- Git (optional, for cloning)

### Step 1 — Get the files

Either clone from GitHub:
```bash
git clone https://github.com/YOUR_USERNAME/nepal-election-2082.git
cd nepal-election-2082
```
Or download and unzip the files manually.

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Run setup (installs Playwright browser)
```bash
python setup.py
```

### Step 4 — Start the app
```bash
python app.py
```

### Step 5 — Open in browser
```
http://127.0.0.1:7860
```

> **Note:** The first run will take a minute to fetch data as Playwright
> launches a headless browser to render the EC website.

---

## 🤗 Deploy on Hugging Face Spaces (Free)

Hugging Face Spaces hosts Gradio apps for free with no credit card required.

### Step 1 — Create a Hugging Face account
Sign up at [huggingface.co](https://huggingface.co) — it's free.

### Step 2 — Create a new Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Give it a name, e.g. `nepal-election-2082`
3. Select **Gradio** as the SDK
4. Set visibility to **Public**
5. Click **Create Space**

### Step 3 — Upload files
Upload all of the following files to your Space:

```
app.py
requirements.txt
packages.txt
README.md
LICENSE
.gitignore
```

You can upload via the **Files** tab in your Space, or link it to your GitHub repo
(Settings → Repository → Link to GitHub).

### Step 4 — Wait for build
Hugging Face will automatically install all dependencies and launch the app.
Build typically takes 2–5 minutes. Your app will be live at:

```
https://huggingface.co/spaces/YOUR_USERNAME/nepal-election-2082
```

---

## 📁 File Structure

```
nepal-election-2082/
├── app.py              # Main Gradio application
├── setup.py            # One-time local setup script
├── requirements.txt    # Python dependencies
├── packages.txt        # System packages for Hugging Face (Chromium)
├── README.md           # This file
├── LICENSE             # MIT License
└── .gitignore
```

---

## 🔧 Tech Stack

| Tool | Purpose |
|---|---|
| [Gradio](https://gradio.app) | Web UI framework |
| [Playwright](https://playwright.dev/python/) | Headless browser to render the EC website |
| [Plotly](https://plotly.com/python/) | Interactive pie charts |
| [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| [Pandas](https://pandas.pydata.org) | Data processing |

---

## 📜 License

MIT License — free to use, modify, and share.
See [LICENSE](./LICENSE) for full terms.

---

## 🔗 Data Source

All data is sourced exclusively from the official
**[Election Commission of Nepal](https://result.election.gov.np/PRVoteChartResult2082.aspx)**.

This project is not affiliated with the Election Commission of Nepal,
any political party, or any government body.