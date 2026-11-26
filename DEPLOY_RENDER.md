# 🚀 Deploy AcadFlow on Render.com

## Environment Variables (Render Dashboard → Environment)

Remove any old `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` / `GROQ_API_KEY` variables and configure:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | `YOUR_NEW_PRIVATE_API_KEY` |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `DATABASE_PATH` | `/data/campus.db` |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma` |
| `DOCUMENT_STORAGE_PATH` | `/data/uploads` |
| `ADMIN_PASSWORD` | `YourStrongAdminPassword` |
| `OFFICER_PASSWORD` | `YourStrongOfficerPassword` |

## Deploy Steps

1. Push your latest code to GitHub:
   ```bash
   git add .
   git commit -m "Upgrade to AcadFlow with Google Gemini"
   git push origin main
   ```
2. In **Render Dashboard → Environment**, add `GEMINI_API_KEY` and `GEMINI_MODEL=gemini-2.5-flash` and click **Save Changes**.
3. Wait 2–4 minutes for the Docker build to finish.
4. Open your Render URL, sign in as `admin`, and upload your institutional PDFs under **Document Manager**.

> **Storage Note:** On Render's Free tier without a Persistent Disk, `/data` is ephemeral and resets on redeploy/restart. Attach a Persistent Disk at `/data` on a paid plan for permanent storage across restarts.
