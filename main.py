import streamlit as st
import pandas as pd
from llm import generate_outreach

st.set_page_config(page_title="CSV Upload", page_icon="📄", layout="centered")
st.title("CSV File Upload")

# What we're actually proposing
PARTNERSHIP_GOAL = f"""Armature Labs is looking to onboard {{recipient_company}} as a paid pilot partner. 
In exchange for access to relevant lab data and operational visibility, 
Armature will implement their system at cost — connecting {{recipient_company}}'s existing tools, 
automating routine documentation tasks, and providing engineering support throughout.
"""


uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type=["csv"],
    help="Choose a .csv file to load into a dataframe.",
)
df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df[["vendor_name", "address", "description", "linkedin_url", "linkedin_name", "linkedin_about_us", "linkedin_website", "linkedin_phone",
        "linkedin_industry", "linkedin_company_type", "linkedin_specialties", "linkedin_headcount"]]
        desc = df["description"].fillna("").astype(str)
        about = df["linkedin_about_us"].fillna("").astype(str)
        df["full_description"] = (desc + "\n" + about).str.strip().replace("\n\n+", "\n", regex=True)
        df["description"] = desc.replace("\n", " ", regex=False)
        df["linkedin_about_us"] = about.replace("\n", " ", regex=False)
        st.success(f"Loaded **{len(df)}** rows and **{len(df.columns)}** columns.")
        st.dataframe(df, width="stretch")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        df = None
else:
    st.info("Upload a .csv file to see its contents.")

recipient_name = st.text_input("Enter the name of the recipient", "Peter Chater")
recipient_role = st.text_input("Enter the role of the recipient", "CEO")
recipient_company = st.text_input("Enter the company of the recipient", "Aelius Biotech Limited")
partnership_goal = st.text_input("Enter the goal of the partnership", PARTNERSHIP_GOAL)
options = st.multiselect(
    "What style/tone shoudl the email be?",
    ["Direct", "Warm", "Friendly", "Professional", "Technical", "Humorous", "Non-technical"],
    default=["Direct", "Warm", "Professional"],
)
if st.button("Generate email", width="stretch"):
    if df is not None:
        result = generate_outreach(df, recipient_name, recipient_role, recipient_company, partnership_goal, options)
        st.subheader("Subject")
        st.write(result["subject"])
        st.subheader("Email")
        st.text(result["final_message"])
    else:
        st.warning("Upload a CSV file first.")