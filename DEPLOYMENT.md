# Deployment Guide: Hugging Face Spaces (Free)

This guide will help you deploy your **Five Boroughs Hub** project (Python Backend + React Frontend) to **Hugging Face Spaces** for free.

## Prerequisites
- A [Hugging Face](https://huggingface.co/) account.
- Your Gemini API Key.

## Step 1: Create a New Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. **Name**: `five-boroughs-hub` (or any name you like).
3. **SDK**: Select **Docker**.
4. **License**: Apache 2.0 or MIT (optional).
5. **Visibility**: Public or Private.
6. Click **"Create Space"**.

## Step 2: Upload Files
You can upload files via the web interface or Git.

### Option A: Web Interface (Easiest for first time)
1. On your Space page, click **"Files"**.
2. Click **"Add file"** -> **"Upload files"**.
3. Drag and drop **ALL** files from your `FiveBoroughs-Hub` directory into the upload area.
   - Important: Ensure you include `Dockerfile`, `requirements.txt`, `app.py`, and the entire `frontend` folder.
   - Note: You do NOT need to upload `node_modules`, `frontend/node_modules`, `frontend/dist`, or `.env`. The Docker build handles these.
4. Click **"Commit changes to main"**.

### Option B: Git Command Line
1. Clone your Space locally (command shown on the Space page).
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/five-boroughs-hub
   ```
2. Copy your project files into this new folder.
3. Commit and push:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push
   ```
   *Note: When asked for your password, you MUST use a **Hugging Face Access Token** with `write` permissions. You can create one in your [Hugging Face Settings](https://huggingface.co/settings/tokens).*

## Step 3: Configure Secrets (Environment Variables)
1. On your Space page, go to **"Settings"**.
2. Scroll to the **"Variables and secrets"** section.
3. Click **"New secret"** and add:
   - Name: `GEMINI_API_KEY`
   - Value: (Your Gemini API Key starting with `AIza...`)
4. Add any other secrets from your `.env` file (e.g., `SECRET_KEY`).

## Step 4: Watch it Build
1. Click the **"App"** tab.
2. You will see a "Building" status.
3. The Docker process will:
   - Install Node.js and build your React frontend.
   - Install Python dependencies.
   - Start the server.
4. Once "Running", your app is live!

---

## Troubleshooting
- **Build Fails?** Check the **"Logs"** tab.
- **"Application Error"?** Ensure `GEMINI_API_KEY` is set in Secrets, not just as a Variable.
