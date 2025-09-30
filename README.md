# 🕵️‍♂️ Twitter Crawler Streamlit

A research-oriented web app for crawling data from **Twitter/X** to support **Fake News Detection** and other NLP tasks.  
Built with **Python 3.11 + Streamlit + Playwright + SQLAlchemy + MySQL**.

---

## 🚀 Features

- 🎛 **Streamlit UI**

  - Sidebar: input cookies (JSON), crawler configuration.
  - Tabs:
    - **Search**: crawl tweets by keyword.
    - **User**: crawl tweets from a specific user.
    - **Dashboard**: display statistics, pagination, and filtering.

- 🕸 **Crawler powered by Playwright**

  - Simulates a real Chromium browser.
  - Automatic scrolling to load more tweets.
  - Checkpoint system to avoid duplicate crawls.

- 💾 **Data persistence**

  - Export crawled data as CSV / JSONL.
  - Save into **MySQL** (auto-create table if missing).
  - **Upsert** logic to prevent duplicate `post_id`.

- 📊 **Dashboard**
  - Explore all collected tweets.
  - Paginated table view.
  - Filtering by date range and keyword.

---

## 🛠 Requirements

- Python **3.11** (recommend Miniconda/Conda env).
- Node.js & Chromium (required by Playwright).
- MySQL (5.7+ or 8.x).

---

## 📦 Installation

### 1. Clone repository

```bash
git clone https://github.com/XT-xuantruong/twitter_crawler_streamlit.git
cd social_crawler_streamlit
```

### 2. Create Conda environment

```bash
conda create -n crawler python=3.11 -y
conda activate crawler
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install browser for Playwright

```bash
playwright install chromium
```

## ⚙️ Configuration

### Create a `.env` file in the project root:

```env
# MySQL connection string
MYSQL_URL=mysql+pymysql://username:password@host:3306/social_crawler?charset=utf8mb4
```

### ▶️ Run the app

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Open in browser:
👉 http://localhost:8501

## 📂 Project Structure

```pgsql
social_crawler_streamlit/
│── app.py                # Main Streamlit entry point
│
├── core/
│   └── config.py          # Global configuration (MySQL, user-agents, timing)
│
├── services/
│   ├── browser.py         # Playwright browser launcher
│   └── twitter_playwright.py # Main crawler
│
├── storage/
│   └── db.py              # MySQL connector and upsert logic
│
├── utils/
│   ├── io.py              # Export CSV/JSONL helpers
│   ├── schema.py          # Record normalization
│   ├── checkpoint.py      # Deduplication checkpoint
│   └── twitter_helpers.py # Helpers (metrics parsing, cookie normalization)
│
└── ui/
    ├── sidebar_ui.py      # Sidebar (cookies, settings)
    ├── search_ui.py       # Search tab
    ├── user_ui.py         # User tab
    └── dashboard_ui.py    # Dashboard tab
```

## 🧪 Usage Examples

### Crawl by keyword

- Enter keyword: fake news

- Max posts: 200

- Click Start Crawl

- Export as CSV or save to DB.

### Crawl by user

- Username: BBCNews

- Max posts: 300

- Check results in Dashboard tab.

## ⚠️ Notes

### Cookies

- You must log in to x.com using Chromium, export cookies, and ensure the JSON file contains at least:

  - "auth_token"

  - "ct0"

- Without these cookies, X will block access to search.

### Cookie expiration

- If cookies expire, re-login via Chromium and save again.

### Rate limiting

- X/Twitter enforces rate limits.

- For larger datasets: rotate cookies/accounts, use proxies, or request official API access.

### MySQL

- If you encounter nan can not be used with MySQL, it has been fixed by converting NaN → NULL before inserting.
