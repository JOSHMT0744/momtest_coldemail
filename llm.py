import outlines
import sys
import threading
import time
import torch
import re
import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen3-4B-Thinking-2507"
logger.info("Loading tokenizer and model: {}", model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
hf_model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16
)
logger.info("Wrapping model in Outlines")
model = outlines.from_transformers(hf_model, tokenizer)
logger.success("Model ready")


# Schema for structured cold-email slots (chain-of-thought + template fields)
class OutreachSchema(BaseModel):
    thinking: str = Field(
        description=(
            "Internal chain-of-thought reasoning. Use COMPANY EMPLOYEE COUNT and COMPANY INDUSTRY "
            "to reason about scaling bottlenecks (e.g. compliance/documentation strain at 50–200 people in biotech). "
            "Never appears in the final email."
        )
    )
    subject_growth_signal: str = Field(
        description=(
            "Short phrase for the email subject line, relevant to the company (e.g. 'Team expansion in regulatory'). "
            "No greetings or sign-offs. One short phrase only."
        )
    )
    partnership_goal: str = Field(
        description=(
            "One paragraph eliciting the partnership goal and the recipient's ROI from engaging with Armature Labs. "
            "Can open with a signal/challenge line (e.g. 'Saw X. When [role/team]s scale fast, [challenge] tends to show up.') "
            "then the partnership pitch. No greetings, no sign-offs. Standalone paragraph only."
        )
    )
    social_proof_line: str = Field(
        description=(
            "One sentence: 'We helped [Similar Company] [specific result or %] without adding more work to the team.' "
            "Must name a similar company and a concrete result or percentage. No greetings or sign-offs."
        )
    )

# Sender details
SENDER_NAME    = "Josh"
SENDER_ROLE    = "Co-Founder"
SENDER_COMPANY = "Armature Labs"

# What our company does — short version to keep prompts lean
SENDER_COMPANY_CONTEXT = (
    "Armature Labs: AI middleware for regulated biotech — connects ELN/LIMS/QMS, automates compliance docs "
    "(deviations, approvals, anomaly flagging). Reduces admin burden while staying audit-ready. Pilot stage; seeking CRO partners."
)

# What we're actually proposing (used in script test and as default in Streamlit)
PARTNERSHIP_GOAL = (
    "Armature Labs is looking to onboard BioAxis as a paid pilot partner. "
    "In exchange for access to relevant lab data and operational visibility, "
    "Armature will implement their system at cost — connecting BioAxis's existing tools, "
    "automating routine documentation tasks, and providing engineering support throughout. "
    "The immediate ask is an introductory call to establish fit and discuss scope."
)

# Max chars for company description in prompt (long descriptions bloat context)
MAX_COMPANY_DESC_CHARS = 600


def _get_company_context(df: pd.DataFrame, recipient_company: str) -> tuple[str, str, str]:
    """Resolve company row and return (description, headcount, industry) with fallbacks."""
    logger.debug("Resolving company context for {}", recipient_company)
    mask = df["vendor_name"].str.lower().str.strip() == recipient_company.lower().strip()
    if not mask.any():
        logger.warning("No row found for company '{}'", recipient_company)
        return "Not specified", "Not specified", "Not specified"
    row = df.loc[mask].iloc[0]
    desc = row.get("full_description")
    if pd.isna(desc) or (isinstance(desc, str) and not desc.strip()):
        parts = []
        if pd.notna(row.get("description")) and str(row.get("description", "")).strip():
            parts.append(str(row["description"]).strip())
        if pd.notna(row.get("linkedin_about_us")) and str(row.get("linkedin_about_us", "")).strip():
            parts.append(str(row["linkedin_about_us"]).strip())
        desc = "\n".join(parts) if parts else "Not specified"
    else:
        desc = str(desc).strip()
    headcount = row.get("linkedin_headcount")
    if pd.isna(headcount) or headcount is None or str(headcount).strip() == "":
        headcount = "Not specified"
    else:
        headcount = str(headcount).strip()
    industry = row.get("linkedin_industry")
    if pd.isna(industry) or industry is None or str(industry).strip() == "":
        industry = "Not specified"
    else:
        industry = str(industry).strip()
    return desc, headcount, industry


def generate_outreach(
    df: pd.DataFrame,
    recipient_name: str,
    recipient_role: str,
    recipient_company: str,
    partnership_goal: str,
    style: list[str],
) -> dict:
    logger.info("Starting outreach generation: {} → {}", SENDER_COMPANY, recipient_company)
    style_str = ", ".join(style) if isinstance(style, list) else str(style)
    company_desc, company_headcount, company_industry = _get_company_context(df, recipient_company)
    if len(company_desc) > MAX_COMPANY_DESC_CHARS:
        company_desc = company_desc[: MAX_COMPANY_DESC_CHARS].rsplit(" ", 1)[0] + "…"
    logger.debug("Company context: headcount={}, industry={}", company_headcount, company_industry)

    context = f"""SENDER: {SENDER_NAME}, {SENDER_ROLE} @ {SENDER_COMPANY}
SENDER_CTX: {SENDER_COMPANY_CONTEXT}
RECIPIENT: {recipient_name}, {recipient_role} @ {recipient_company}
CO: {recipient_company} | HC: {company_headcount} | IND: {company_industry}
DESC: {company_desc}
GOAL: {partnership_goal}
STYLE: {style_str}""".strip()

    prompt = f"""<|im_start|>system
You output JSON only. Use HC and IND in 'thinking' to reason about scaling bottlenecks. Slot fields: no greetings/sign-offs. Reasoning only in 'thinking'. partnership_goal = one paragraph; social_proof_line = one sentence with similar company + result or %.
<|im_end|>
<|im_start|>user
SENDER: James, BD Lead @ PharmaPath CRO.
SENDER_CTX: PharmaPath: CRO for CNS/rare-disease recruitment; 40 US sites.
RECIPIENT: Dr. Chen, Alliance Director @ TrialBridge CRO.
CO: TrialBridge CRO | HC: 75 | IND: Biotechnology / Clinical Research
DESC: Large neurology portfolio, expanding rare disease; recruitment speed and compliance doc burden are bottlenecks.
GOAL: Explore automating their TrialBrdige's data backbone, allowing them to interact with AI to generate deterministic, 100% reliable necessary documentation. Ask: 20-min call.
STYLE: Professional, specific, no buzzwords.
<|im_end|>
<|im_start|>assistant
{{"thinking": "75 employees in biotech: compliance/doc burden is a scaling bottleneck. Lead with their problem, tie to growth.", 
"subject_growth_signal": "Rare disease Deviation Policy Automation at Scale", 
"partnership_goal": "Saw you're expanding rare disease — when clinical ops scale fast, recruitment and back-office doc burden tend to spike. A short call could clarify whether a referral arrangement makes sense, with you keeping sponsor oversight.", 
"social_proof_line": "We helped a similar-sized CRO cut deviation timelines ~30% without adding headcount by routing studies into our network."}}
<|im_end|>
<|im_start|>user
{context}
<|im_end|>
<|im_start|>assistant
"""

    max_new_tokens = 358
    logger.info("Running model (max_new_tokens={})", max_new_tokens)

    def _spinner(stop: threading.Event) -> None:
        chars = "|/-\\"
        i = 0
        start = time.monotonic()
        while not stop.is_set():
            elapsed = time.monotonic() - start
            sys.stderr.write(f"\r  Generating tokens... {chars[i % 4]} ({elapsed:.0f}s)   ")
            sys.stderr.flush()
            i += 1
            time.sleep(0.2)
        sys.stderr.write("\r" + " " * 50 + "\r")
        sys.stderr.flush()

    spinner_stop = threading.Event()
    spinner_thread = threading.Thread(target=_spinner, args=(spinner_stop,), daemon=True)
    spinner_thread.start()
    try:
        raw = model(prompt, OutreachSchema, max_new_tokens=max_new_tokens)
    finally:
        spinner_stop.set()
        spinner_thread.join(timeout=1.0)

    logger.debug("Raw model output received ({} chars)", len(raw))
    cleaned_raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    response = OutreachSchema.model_validate_json(cleaned_raw)
    logger.info("Parsed structured response")

    first_name = recipient_name.split()[0] if recipient_name.strip() else recipient_name
    subject = f"{response.subject_growth_signal} at {recipient_company}"

    partnership_goal_clean = response.partnership_goal
    for bad in ["Hey ", "Hi ", "Hello ", "Dear "]:
        if partnership_goal_clean.startswith(bad):
            partnership_goal_clean = partnership_goal_clean[len(bad):].strip()
    for bad in ["Best regards", "Thanks", "Regards", "Cheers"]:
        if bad in partnership_goal_clean and partnership_goal_clean.rstrip().endswith(bad):
            partnership_goal_clean = partnership_goal_clean[: partnership_goal_clean.rfind(bad)].rstrip()

    final_message = (
        f"Hi {first_name}\n\n"
        f"{partnership_goal_clean}\n\n"
        f"{response.social_proof_line}\n\n"
        "Would you be open to a quick 15-min chat? Feel free to book via my Calendly link below\n\n {CALENDLY_LINK}\n\n"
        "Best regards,\n\n"
        f"{SENDER_NAME}\n"
        f"{SENDER_ROLE}, Armature Labs\n"
        "www.armaturelabs.ai"
    )

    logger.info("Assembled final email")
    logger.opt(raw=True).info("Thinking: {}", response.thinking)
    logger.opt(raw=True).info("Subject: {}", subject)
    logger.opt(raw=True).info("Body:\n{}", final_message)
    logger.success("Outreach generation complete")

    return {
        "thinking": response.thinking,
        "subject": subject,
        "final_message": final_message,
        "subject_growth_signal": response.subject_growth_signal,
        "partnership_goal": response.partnership_goal,
        "social_proof_line": response.social_proof_line,
    }


# When run as script, use minimal test data (real usage is via Streamlit app)
if __name__ == "__main__":
    test_df = pd.DataFrame([
        {
            "vendor_name": "BioAxis Research",
            "description": "Mid-size CRO, Phase I–III oncology trials.",
            "linkedin_about_us": "In-house biomarker profiling, growing regulatory affairs team.",
            "full_description": "Mid-size CRO, Phase I–III oncology trials.\nIn-house biomarker profiling, growing regulatory affairs team.",
            "linkedin_headcount": "150",
            "linkedin_industry": "Biotechnology",
        }
    ])
    logger.info("Running script test")
    result = generate_outreach(
        test_df,
        recipient_name="Sarah",
        recipient_role="VP of Strategic Alliances",
        recipient_company="BioAxis Research",
        partnership_goal=PARTNERSHIP_GOAL,
        style=["Direct", "Warm", "Professional"],
    )
    logger.info("Test result: {}", result["final_message"])