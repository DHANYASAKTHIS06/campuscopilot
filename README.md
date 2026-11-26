# 🎓 AcadFlow
### Intelligence That Moves Academia Forward.

**AcadFlow** is an AI-powered institutional intelligence platform that simplifies academic information, document intelligence, eligibility assessment, planning, and institutional support.

---

## ✨ Features

- **Google Gemini AI (`google-genai`):** Centralized Gemini configuration (`gemini-3.5-flash-lite`) with timeout, retry, quota, and error handling.
- **Dual-Mode Conversational AI:**
  - *Normal Conversation Mode:* Natural greetings and casual follow-up chats without unnecessary document searches.
  - *Document-Based RAG Mode:* Strict institutional answering with clickable citations and page numbers.
- **Hybrid RAG Pipeline:** Combines **BM25** keyword search + **ChromaDB** vector search using **Reciprocal Rank Fusion (RRF)** and **lexical reranking**.
- **Multi-Agent Architecture:** Orchestrator, Hybrid Retrieval, Knowledge & Synthesis, Eligibility, Planning, Verification, Revision, Recovery, Application Letter Drafting, and Helpdesk Officer Assistant.
- **Role-Based Dashboards:** Dedicated experiences for **Students**, **Administrators**, and **Helpdesk Officers**.
- **Security & Trust:** PBKDF2 password hashing, 7-day session tokens, server-side role authorization, PDF validation, and prompt-injection scanning.

---

## 🛠️ Technology Stack

- **Frontend / UI:** Streamlit (custom SaaS design system)
- **LLM Provider:** Google Gemini (`google-genai`)
- **Vector Store & Search:** ChromaDB + BM25 + RRF + Lexical Reranking
- **PDF Processing:** PyMuPDF (`pymupdf`) + ReportLab A4 PDF export
- **Database:** SQLite (WAL mode)

---

## 🚀 Local Development

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env         # Windows (or cp .env.example .env)
# Edit .env and set GEMINI_API_KEY=YOUR_NEW_PRIVATE_API_KEY

# 4. Run AcadFlow
streamlit run app.py
```

Default credentials (override via `ADMIN_PASSWORD` / `OFFICER_PASSWORD`):
- **Admin:** `admin` / `admin123`
- **Helpdesk Officer:** `officer` / `officer123`

---

## ☁️ Render Deployment

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for full step-by-step instructions.

### Required Render Environment Variables
| Key | Value |
|---|---|
| `GEMINI_API_KEY` | `YOUR_NEW_PRIVATE_API_KEY` |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` |
| `DATABASE_PATH` | `/data/campus.db` |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma` |
| `DOCUMENT_STORAGE_PATH` | `/data/uploads` |
| `ADMIN_PASSWORD` | Strong password |
| `OFFICER_PASSWORD` | Strong password |

*(For persistent storage across redeploys, attach a Render Persistent Disk mounted at `/data` on a paid plan; on the Free tier, `/data` uses temporary container storage.)*

---

## 🧪 Testing

```bash
# Run retrieval evaluation
python eval/run_eval.py --mode retrieval

# Run full pipeline evaluation
python eval/run_eval.py --mode full --limit 10
```
