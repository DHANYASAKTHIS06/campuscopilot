# 🚀 Deploy CampusCopilot on Render.com (Free Tier — No Disk)

> **Time needed:** ~10–15 minutes  
> **Cost:** Free (Render free tier, ephemeral storage)  
> **Result:** A public HTTPS URL like `https://campuscopilot-xxxx.onrender.com`

---

## Prerequisites

1. A **GitHub account** — [github.com](https://github.com)
2. A **Render account** — [render.com](https://render.com) (sign up free with GitHub)
3. An **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)

---

## Step 1: Push Your Code to GitHub

1. Create a new **Private** repository named `campuscopilot` on [github.com/new](https://github.com/new) (do **not** add a README).
2. In your project folder (`d:\Desktop\project\campuscopilot`), run:

```bash
git init
git add .
git commit -m "CampusCopilot - production ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/campuscopilot.git
git push -u origin main
```

---

## Step 2: Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Select **"Build and deploy from a Git repository"** → **Next**
4. Connect your GitHub account and select **`campuscopilot`**
5. Configure:
   - **Name:** `campuscopilot`
   - **Region:** Closest to you (e.g., `Singapore`)
   - **Branch:** `main`
   - **Runtime:** **Docker**
   - **Instance Type:** **Free**
6. Click **"Create Web Service"**

---

## Step 3: Set Environment Variables (Skip Disks)

Since you are deploying **without a persistent disk** (Free tier), skip the Disks section and go straight to **Environment**:

1. In your Render service dashboard, click **"Environment"** in the left sidebar.
2. Click **"Add Environment Variable"** and add these variables:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-your-real-key` |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` |
| `DATABASE_PATH` | `/data/campus.db` |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma` |
| `DOCUMENT_STORAGE_PATH` | `/data/uploads` |
| `ADMIN_PASSWORD` | `YourStrongPassword123` |
| `OFFICER_PASSWORD` | `YourStrongPassword456` |

3. Click **"Save Changes"** (this triggers a redeploy automatically).

---

## Step 4: Wait for Deployment

1. Click **"Events"** in the left sidebar to watch the build logs.
2. Wait 3–5 minutes until you see **"Your service is live 🎉"**.
3. Click the public URL shown at the top of the page:
   `https://campuscopilot-xxxx.onrender.com`

---

## Step 5: First-Time Setup & Testing

1. Open your public URL.
2. Sign in as **`admin`** with the `ADMIN_PASSWORD` you set in Step 3.
3. Go to **Documents → Upload & Index**, upload your college PDFs, and click **Upload & Process**.
4. Sign out, register a student account under **Create Account**, and test **AI Chat**.

> **Important Note (No Disk):** On the Free tier without a persistent disk, uploaded PDFs, student accounts, and ChromaDB data are stored in temporary container storage (`/data`). Whenever Render restarts or redeploys your service, this data resets and you will need to re-upload your PDFs.
