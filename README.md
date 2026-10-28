# AI Study Assistant

A Python + Streamlit app that turns lecture notes into exam revision materials using the Gemini API. It extracts text from PDF, TXT, and Markdown files with PyMuPDF and can generate summaries, MCQs, short questions with answers, interactive flashcards, and a personalized exam preparation plan.

## Features

- Upload PDF, TXT, and Markdown notes.
- Extract and preview readable text from PDFs.
- Generate exam-friendly summaries.
- Generate multiple-choice questions with correct answers and explanations.
- Generate short questions with answers.
- Create interactive flashcards with reveal, previous, next, and reset controls.
- Build a study plan from exam date, daily available hours, and a topic list.
- Download generated study materials as Markdown or JSON.

## Requirements

- Python 3.10 or newer (Python 3.11 recommended).
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- Internet access for Gemini requests.

## Run locally (Windows)

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/). During setup, select **Add Python to PATH**.
2. Download or clone this repository and open its folder in Command Prompt or VS Code.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   streamlit run app.py
   ```

6. Streamlit opens the app in your browser, usually at `http://localhost:8501`.
7. Paste your Gemini API key into the sidebar. Alternatively, set an environment variable before starting Streamlit:

   ```powershell
   $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
   streamlit run app.py
   ```

Do not commit your API key to GitHub.

## Upload to GitHub (browser / GUI method)

1. Sign in at [GitHub](https://github.com/) and create a **new public or private repository**, for example `ai-study-assistant`.
2. In the repository page, choose **Add file → Upload files**.
3. Upload `app.py`, `requirements.txt`, and `README.md`. You can also upload a `.gitignore` file.
4. Review the file list, enter a commit message such as `Add AI Study Assistant`, and click **Commit changes**.
5. Check that the repository contains the three files at its root.

Recommended `.gitignore` contents:

```gitignore
.venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
.env
```

## Deploy on Streamlit Community Cloud

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with your GitHub account.
3. Select **Create app** (or **Deploy an app**).
4. Choose the repository, branch (usually `main`), and main file path `app.py`.
5. Open **Advanced settings / Secrets** before or after deployment and add:

   ```toml
   GEMINI_API_KEY = "YOUR_REAL_GEMINI_API_KEY"
   ```

6. Deploy the app. Streamlit installs packages from `requirements.txt`.
7. Open the app URL and test with a small, text-based PDF. Entering the key in the sidebar is also supported.

If you change code in GitHub, Streamlit Community Cloud normally rebuilds/redeploys the app automatically.

## How to use

1. Add your Gemini API key in the sidebar or configure Streamlit secrets.
2. Upload a PDF, TXT, or Markdown file containing lecture notes.
3. Choose a tab: Summary, MCQs, Short questions, Flashcards, or Exam plan.
4. Click the relevant generation button.
5. Download the generated output when available.
6. For the study plan, enter the exam date, daily study hours, and one topic per line.

## Troubleshooting

- **`ModuleNotFoundError`:** Activate the virtual environment and run `pip install -r requirements.txt`.
- **API key missing:** Enter the key in the sidebar, set `GEMINI_API_KEY`, or configure Streamlit Cloud Secrets.
- **Invalid API key / permission error:** Check the key in Google AI Studio and ensure the selected model is available to your account.
- **Quota or rate limit:** Check your Gemini API usage and quota; wait and retry if needed.
- **PDF has no text:** It may be a scanned image. OCR it first, then upload the searchable PDF.
- **Model not found:** Change the model in the sidebar to a Gemini model currently available to your API key.
- **Very long notes:** The app limits the extracted text sent per request to 80,000 characters to reduce oversized requests.

## Notes and limitations

- AI-generated content can contain mistakes. Verify important facts against your course materials.
- The app sends extracted notes to Google Gemini only after you request generation.
- The app does not save uploaded files to a database. Streamlit session state holds the extracted text and generated results for the current session.
- The app currently supports text-based PDFs and UTF-8 text/Markdown files; it does not perform OCR.
