
```markdown
# 📰 News & Text Processing API Project

Welcome to the News & Text Processing API!  
This project provides a FastAPI-based server that processes user texts and news articles by:
- Converting to standard Korean
- Removing slang and inappropriate language
- Summarizing into simple, easy-to-understand language

---
## 🌟 Features

✅ **JSON File Text Processing**  
- Input arbitrary text.
- Standardize Korean.
- Remove profanity and inappropriate expressions.
- Extract key points.

✅ **News Article Processing**  
- Crawl news article content via URL.
- Standardize and simplify language for better accessibility.
- Summarize into simple sentences suitable for general audiences.

✅ **Data Persistence**  
- All processed texts are saved in a SQLite database for future retrieval and analysis.

---
## 🏗️ Project Structure

```
/project-root
│
├── main.py             # FastAPI server (API endpoints)
├── models.py           # SQLAlchemy ORM models (ProcessedText table)
├── database.py         # Database connection management
├── requirements.txt    # Dependency list
├── /crawling
│   ├── newscrawling.py  # News crawling module
│   └── keyword.py       # Keyword extraction module
├── /utils
│   └── text_processor.py  # GPT-powered text refinement and summarization
├── .env                # Environment variables (OpenAI API Key)
└── README.md           # Project documentation
```

---
## ⚙️ Installation

1. **Clone the Repository**
```bash
git clone https://github.com/your-username/news-text-processing-api.git
cd news-text-processing-api
```

2. **Create Virtual Environment (Optional but Recommended)**
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. **Install Required Packages**
```bash
pip install -r requirements.txt
```

4. **Set up `.env`**
Create a `.env` file in the root directory with your OpenAI API Key:
```plaintext
OPENAI_API_KEY=your-openai-api-key-here
```

---
## 🚀 Running the Server

```bash
uvicorn main:app --reload
```

- Access Swagger UI for API testing at:
  ```
  http://localhost:8000/docs
  ```

---
## 🛠️ API Endpoints

### POST `/process-text/`
**Input:**  
```json
{
  "text": "Input your text here"
}
```
**Output:**  
- Standardized Text
- Cleaned Text (no slang/profanity)
- Summarized Text

---

### POST `/process-news/`
**Input:**  
```json
{
  "url": "https://news.example.com/article123"
}
```
**Output:**  
- News article body standardized
- Cleaned and simplified version
- Summarized main points

---

## 📚 How It Works

- **`/process-text/`**: Processes any user-provided text through OpenAI's GPT-4 Turbo model.
- **`/process-news/`**: Crawls the news content from the given URL, then refines and summarizes it.
- **Database (`processed_texts.db`)**: All processed results are saved with original and cleaned versions for traceability.

---

## 🧠 Tech Stack

- **FastAPI** 🚀 — High performance web framework
- **OpenAI GPT-4 Turbo** 🤖 — Advanced language model
- **SQLAlchemy** 🛢️ — ORM for database interaction
- **SQLite** 🗂️ — Lightweight database
- **BeautifulSoup** 🍲 — Web scraping library for news articles

---

