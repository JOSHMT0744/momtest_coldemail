# Armature Labs Cold Email Generator

A Streamlit app that generates personalized, “mom test”–style cold outreach emails for **Armature Labs**. It uses a local LLM (Qwen) with chain-of-thought and few-shot prompting to produce structured emails tailored to each recipient and their company.

## What it does

- **Upload a CSV** of target companies (e.g. CROs, biotechs) with names, descriptions, headcount, and industry.
- **Enter recipient details** (name, role, company) and the partnership goal you want to convey.
- **Generate an email** that:
  - Uses a **subject line** based on a growth signal relevant to the company.
  - Opens with a **signal/challenge line** (e.g. hiring, scaling, compliance burden) tied to their size and industry.
  - Includes a **partnership paragraph** that explains Armature’s offer and the recipient’s ROI.
  - Adds **social proof** (similar company + concrete result or %).
  - Ends with a **short CTA** and sign-off (Josh, Co-Founder, Armature Labs).

The model uses **employee count** and **industry** from your CSV to reason about scaling bottlenecks and to keep the email specific and credible.

## Prerequisites

- Python 3.10+
- Enough RAM/VRAM to run a ~4B parameter model (e.g. Qwen3-4B). On CPU only, generation can take several minutes per email.

## Setup

1. Clone or open this repo and create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

2. Install dependencies (includes Streamlit, transformers, outlines, loguru, pandas):

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   streamlit run main.py
   ```

   The app opens in your browser (e.g. http://localhost:8501). The first run will download the model; later runs reuse the cached model.

## How to use the app

### 1. Upload a CSV

- Use the **“Upload a CSV file”** widget and choose a `.csv` file.
- The CSV must include at least these columns (names must match):
  - `vendor_name` — Company name (used to match the recipient’s company).
  - `description` — Short company description.
  - `linkedin_about_us` — Extra context (e.g. from LinkedIn).
  - `linkedin_headcount` — Employee count (optional; “Not specified” if missing).
  - `linkedin_industry` — Industry (optional; “Not specified” if missing).

  Other columns (e.g. `address`, `linkedin_url`, `linkedin_name`, …) can be present but are not required for generation.

- After a successful load, you’ll see a success message and a preview table of the data.

### 2. Fill in the form

- **Enter the name of the recipient** — e.g. “Sarah Chen”. The email will use their first name (“Hey Sarah”).
- **Enter the role of the recipient** — e.g. “VP of Strategic Alliances”.
- **Enter the company of the recipient** — Must match a `vendor_name` in your CSV exactly (e.g. “Aelius Biotech Limited”). This is how the app finds that row’s description, headcount, and industry.
- **Enter the goal of the partnership** — Default text is provided; edit it to reflect the specific ask (e.g. pilot partner, intro call). This is sent to the model as the “GOAL” so the email stays on-message.
- **What style/tone should the email be?** — Pick one or more: Direct, Warm, Friendly, Professional, Technical, Humorous, Non-technical. Default is Direct, Warm, Professional.

### 3. Generate the email

- Click **“Generate email”**.
- If no CSV is loaded, you’ll see: “Upload a CSV file first.”
- If a CSV is loaded, the app calls the LLM. A spinner in the terminal shows progress (e.g. “Generating tokens… (45s)”). When it finishes, the page shows:
  - **Subject** — e.g. “Team expansion in regulatory at Aelius Biotech Limited”.
  - **Email** — Full body (greeting, partnership paragraph, social proof, CTA, sign-off with Calendly link and Armature Labs details).

You can change the recipient, company, or goal and click **“Generate email”** again to get a new email. The same CSV can be reused for many companies as long as their names appear in `vendor_name`.

## Generated email structure

Each email follows this pattern:

- **Subject:** `[Growth signal] at [Company]`
- **Body:**  
  - Hey [First name]  
  - [Signal/challenge line + partnership paragraph]  
  - [Social proof: “We helped [Similar Company] [result/%] without adding more work to the team.”]  
  - Would you be open to a quick 15-min chat? (Calendly link)  
  - Best regards, Josh, Co-Founder, Armature Labs, www.armaturelabs.ai  

The model is instructed to use headcount and industry to justify the “bottleneck” and fit of Armature’s offer, so the more accurate your CSV (especially `linkedin_headcount` and `linkedin_industry`), the more relevant the email.

## Tips

- **Company name matching** is case-insensitive and trims spaces, but the value must match a row’s `vendor_name` (e.g. “Aelius Biotech Limited” not “Aelius Biotech” if that’s what’s in the CSV).
- **Long company descriptions** in the CSV are truncated (e.g. to 600 characters) in the prompt to keep generation fast; the model still gets the start of the description.
- **First run** loads the model into memory; subsequent generations in the same session are faster until you restart the app.
- **Logs** (including “Generating tokens…”) appear in the terminal where you ran `streamlit run main.py`, not in the browser.

## Project structure

- `main.py` — Streamlit UI: file upload, form, and call to `generate_outreach`.
- `llm.py` — Model loading, prompt construction, structured generation (Outlines + Pydantic schema), and email assembly. Sender details (Josh, Armature Labs, Calendly link) and max description length are configured here.
- `requirements.txt` — Python dependencies.
