# jadehire_app.py
import streamlit as st
import datetime
import pickle
import os
import json
import base64
from email.mime.text import MIMEText

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv
import google.generativeai as genai

from docx import Document
import PyPDF2
import matplotlib.pyplot as plt

# ---------------------------
# ENV & GENAI
# ---------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
LLM = genai.GenerativeModel("gemini-2.5-flash")

# Combined scope for Calendar + Gmail
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
]

TIMEZONE = "Asia/Kolkata"

# ---------------------------
# Helpers: file readers
# ---------------------------
def read_file_content(uploaded_file):
    """Extract plain text from TXT/DOCX/PDF uploads."""
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    if name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        return "\n".join(pg.extract_text() or "" for pg in reader.pages)
    return uploaded_file.read().decode("utf-8", errors="ignore")

# ---------------------------
# Helpers: Google unified OAuth + services
# ---------------------------
def get_google_service(api_name: str, api_version: str):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret_deep_personal.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build(api_name, api_version, credentials=creds)

def send_email_gmail(to_email: str, subject: str, message_text: str):
    service = get_google_service("gmail", "v1")
    msg = MIMEText(message_text)
    msg["to"] = to_email
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"raw": raw}
    return service.users().messages().send(userId="me", body=body).execute()

# ---------------------------
# AI helpers
# ---------------------------
def ai_extract_schedule(text_input: str):
    prompt = f"""
    Extract scheduling details from the following instruction and return JSON ONLY:

    {{
      "candidate_email": "",
      "panel_email": "",
      "subject": "",
      "body": "",
      "date": "YYYY-MM-DD",
      "time": "HH:MM"
    }}

    Instruction:
    {text_input}
    """
    resp = LLM.generate_content(prompt)
    try:
        txt = resp.text.strip().replace("```json", "").replace("```", "")
        return json.loads(txt)
    except Exception:
        return {}

def ai_screen_resumes_with_match(jd_text: str, resumes_dict: dict):
    combined = "\n\n".join([f"Candidate: {k}\n{v}" for k, v in resumes_dict.items()])
    prompt = f"""
    You are an AI recruiter. Compare the following job description with the candidate's resume
        and provide a suitability percentage match with reasoning.

        Job Description:
        {jd_text}

        Candidate Resume:
        {combined}

        Output format strictly:
        Candidate: <name>
        Match: <percentage>
        Summary: <short reasoning>
    """
    resp = LLM.generate_content(prompt)
    # Track usage locally
    st.session_state["llm_calls"] = st.session_state.get("llm_calls", 0) + 1
    return resp.text

def ai_standardize_resume(candidate_resume: str, jade_format_sample: str):
    prompt = f"""
    Convert the following resume into Jade sample style.
    Keep Summary, Education, Work Experience, Projects, Certificates.

    Jade Sample:
    {jade_format_sample}

    Candidate Resume:
    {candidate_resume}
    """
    resp = LLM.generate_content(prompt)
    st.session_state["llm_calls"] = st.session_state.get("llm_calls", 0) + 1
    return resp.text

def generate_ai_email(name: str, role: str, days_left: int):
    prompt = f"""
    Draft a warm, short email to {name} who accepted {role}.
    Their Day 1 is in {days_left} days. Encourage them.
    """
    resp = LLM.generate_content(prompt)
    st.session_state["llm_calls"] = st.session_state.get("llm_calls", 0) + 1
    return resp.text.strip()

# ---------------------------
# LLM Usage Tracker
# ---------------------------
def estimate_tokens(text: str) -> int:
    """Approximate tokens by word count."""
    return len(text.split())

def track_llm_usage(prompt: str, response: str):
    """Track local token and call usage."""
    in_toks = estimate_tokens(prompt)
    out_toks = estimate_tokens(response)
    st.session_state["llm_calls"] = st.session_state.get("llm_calls", 0) + 1
    st.session_state["llm_in_tokens"] = st.session_state.get("llm_in_tokens", 0) + in_toks
    st.session_state["llm_out_tokens"] = st.session_state.get("llm_out_tokens", 0) + out_toks

def ai_screen_resumes_with_match(jd_text: str, resumes_dict: dict):
    combined = "\n\n".join([f"Candidate: {k}\n{v}" for k, v in resumes_dict.items()])
    prompt = f"""
    You are an AI recruiter...
    Job Description:
    {jd_text}

    Candidate Resumes:
    {combined}
    """
    resp = LLM.generate_content(prompt)
    track_llm_usage(prompt, resp.text)
    return resp.text

def ai_standardize_resume(candidate_resume: str, jade_format_sample: str):
    prompt = f"Convert resume...\n\n{candidate_resume}\n\nJade Sample:\n{jade_format_sample}"
    resp = LLM.generate_content(prompt)
    track_llm_usage(prompt, resp.text)
    return resp.text

def generate_ai_email(name: str, role: str, days_left: int):
    prompt = f"Draft a warm, short email to {name} who accepted {role}..."
    resp = LLM.generate_content(prompt)
    track_llm_usage(prompt, resp.text)
    return resp.text.strip()

# ---------------------------
# STREAMLIT CONFIG
# ---------------------------
st.set_page_config(page_title="JadeHire", page_icon="💼", layout="wide")
st.title("💼 JadeHire - An AI-Powered Talent Acquisition Process")

# Branding caption on top
st.markdown(
    "<h4 style='color:#0073e6; font-weight:bold;'>Delivering Innovation, Driving Impact™</h4>",
    unsafe_allow_html=True
)
menu = [
    "🔍 Resume Screening",
    "📑 Standardization",
    "📅 Scheduling & Coordination",
    "🤝 Post-Offer Candidate Connect",
    "🧠 LLM Utilization",
]
choice = st.sidebar.radio("Modules", menu)

# ====================================================
# 1) Resume Screening
# ====================================================
if choice == "🔍 Resume Screening":
    st.subheader("🔍 AI Resume Screening — % Match + Reasoning")

    jd_mode = st.radio("Job Description input", ["Paste JD", "Browse JD File"], horizontal=True)
    jd_text = st.text_area("Paste Job Description", height=200) if jd_mode == "Paste JD" else ""
    if jd_mode == "Browse JD File":
        jd_file = st.file_uploader("Upload JD (.txt/.docx/.pdf)", type=["txt", "docx", "pdf"])
        if jd_file: jd_text = read_file_content(jd_file)

    resumes = st.file_uploader(
        "Upload Candidate Resumes (.txt/.docx/.pdf)", type=["txt", "docx", "pdf"], accept_multiple_files=True
    )

    if st.button("Start Screening"):
        if not jd_text or not resumes:
            st.warning("Please provide a JD and at least one resume.")
        else:
            resumes_dict = {r.name: read_file_content(r) for r in resumes}
            report = ai_screen_resumes_with_match(jd_text, resumes_dict)
            st.text_area("AI Recruiter Report", value=report, height=350)

            matches = {}
            current = None
            for line in report.splitlines():
                if line.lower().startswith("candidate:"):
                    current = line.split(":", 1)[1].strip()
                elif line.lower().startswith("match:") and current:
                    try:
                        matches[current] = int(line.split(":", 1)[1].replace("%", "").strip())
                    except: pass
            if matches:
                sorted_items = sorted(matches.items(), key=lambda x: x[1], reverse=True)
                fig, ax = plt.subplots()
                ax.barh([k for k, _ in sorted_items], [v for _, v in sorted_items])
                ax.set_xlabel("Suitability %"); ax.set_title("Candidate Suitability vs JD")
                ax.invert_yaxis()
                st.pyplot(fig)

# ====================================================
# 2) Standardization
# ====================================================
elif choice == "📑 Standardization":
    st.subheader("📑 Resume Standardization")
    jade_fmt = st.file_uploader("Upload Jade Sample Format", type=["txt", "docx", "pdf"])
    cand_res = st.file_uploader("Upload Candidate Resume", type=["txt", "docx", "pdf"])
    if st.button("Convert"):
        if jade_fmt and cand_res:
            out_text = ai_standardize_resume(read_file_content(cand_res), read_file_content(jade_fmt))
            st.text_area("Standardized Resume", value=out_text, height=380)
            st.download_button("📥 Download DOCX", out_text.encode(), "standardized_resume.docx")
            st.download_button("📥 Download PDF", out_text.encode(), "standardized_resume.pdf")
        else:
            st.warning("Upload both files.")

# ====================================================
# 3) Scheduling & Coordination
# ====================================================
# =========================================
# 3) SCHEDULING & COORDINATION
# =========================================
elif choice == "📅 Scheduling & Coordination":
    st.subheader("📅 AI-Powered Scheduling & Coordination (Google Calendar)")

    tabs = st.tabs(["Schedule", "Reschedule", "History", "Reminders", "Feedback"])

    # ---------- Schedule ----------
    with tabs[0]:
        st.write("### Create New Schedule")
        instr = st.text_area(
            "Enter scheduling instruction (AI will parse)",
            value="Schedule interview with candidate jane.doe@example.com and panel lead@jadehire.com on Friday at 3pm IST for Data Engineer.",
        )
        if st.button("AI Extract Details"):
            parsed = ai_extract_schedule(instr)
            if parsed:
                st.session_state.update(parsed)
                st.success("Details parsed. Review below.")

        cand = st.text_input("Candidate Email", value=st.session_state.get("candidate_email", ""))
        panel = st.text_input("Panel Email", value=st.session_state.get("panel_email", ""))
        subject = st.text_input("Subject", value=st.session_state.get("subject", "Interview with JadeHire"))
        body = st.text_area("Body", value=st.session_state.get("body", "Please join at the scheduled time."))
        date = st.date_input("Date", datetime.date.today())
        time = st.time_input("Time", datetime.time(10, 0))

        if st.button("Save & Send"):
            service = get_google_service("calendar", "v3")
            start_dt = datetime.datetime.combine(date, time)
            end_dt = start_dt + datetime.timedelta(hours=1)
            event = {
                "summary": subject,
                "description": body,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
                "attendees": [{"email": cand}] + ([{"email": panel}] if panel else []),
            }
            ev = service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
            st.success(f"Event created ✅  →  {ev.get('htmlLink')}")

    # ---------- Reschedule ----------
    with tabs[1]:
        st.write("### Reschedule (search by candidate email)")
        search_email = st.text_input("Candidate email to search")
        new_date = st.date_input("New Date", datetime.date.today())
        new_time = st.time_input("New Time", datetime.time(11, 0))

        if st.button("Find Candidate Events"):
            service = get_google_service("calendar", "v3")
            now = datetime.datetime.utcnow().isoformat() + "Z"
            res = service.events().list(
                calendarId="primary", timeMin=now, maxResults=50, singleEvents=True, orderBy="startTime"
            ).execute()
            items = res.get("items", [])
            matches = [
                e for e in items
                if any(att.get("email", "").lower() == search_email.lower() for att in e.get("attendees", []))
            ]
            if not matches:
                st.warning("No upcoming events for that candidate.")
            else:
                st.session_state["found_events"] = matches
                labels = [f"{e.get('summary','(no title)')} — {e['start'].get('dateTime','')}" for e in matches]
                st.session_state["sel_idx"] = st.selectbox("Select event to reschedule", list(range(len(labels))),
                                                           format_func=lambda i: labels[i])

        if "found_events" in st.session_state and st.button("Update Schedule"):
            idx = st.session_state.get("sel_idx", 0)
            event = st.session_state["found_events"][idx]
            service = get_google_service("calendar", "v3")
            start = datetime.datetime.combine(new_date, new_time)
            end = start + datetime.timedelta(hours=1)
            event["start"]["dateTime"] = start.isoformat()
            event["start"]["timeZone"] = TIMEZONE
            event["end"]["dateTime"] = end.isoformat()
            event["end"]["timeZone"] = TIMEZONE
            upd = service.events().update(calendarId="primary", eventId=event["id"], body=event, sendUpdates="all").execute()
            st.success(f"Rescheduled ✅  →  {upd.get('htmlLink')}")

    # ---------- History ----------
    with tabs[2]:
        st.write("### Past Events (last 12 months)")
        service = get_google_service("calendar", "v3")
        now = datetime.datetime.utcnow()
        start = (now - datetime.timedelta(days=365)).isoformat() + "Z"
        end = now.isoformat() + "Z"
        res = service.events().list(
            calendarId="primary", timeMin=start, timeMax=end, maxResults=100, singleEvents=True, orderBy="startTime"
        ).execute()
        events = res.get("items", [])
        if not events:
            st.info("No past events found.")
        else:
            for e in events:
                when = e["start"].get("dateTime", e["start"].get("date"))
                st.write(f"- **{e.get('summary','(no title)')}** — {when}")

    # ---------- Reminders ----------
    with tabs[3]:
        st.write("### Upcoming Events (next 30 days) + Email Reminder")
        service = get_google_service("calendar", "v3")
        now = datetime.datetime.utcnow()
        start = now.isoformat() + "Z"
        end = (now + datetime.timedelta(days=30)).isoformat() + "Z"
        res = service.events().list(
            calendarId="primary", timeMin=start, timeMax=end, maxResults=50, singleEvents=True, orderBy="startTime"
        ).execute()
        events = res.get("items", [])
        if not events:
            st.info("No upcoming events.")
        else:
            labels = [f"{e.get('summary','(no title)')} — {e['start'].get('dateTime','')}" for e in events]
            sel = st.selectbox("Select event to remind", list(range(len(labels))), format_func=lambda i: labels[i])
            if st.button("Send Reminder Email to Attendees"):
                e = events[sel]
                subject = f"Reminder: {e.get('summary','Interview')}"
                when = e["start"].get("dateTime", "")
                attendees = [a.get("email") for a in e.get("attendees", []) if a.get("email")]
                sent_to = []
                for addr in attendees:
                    body = f"Reminder for: {e.get('summary','Interview')}\nWhen: {when}\n\nSee invite for details."
                    try:
                        send_email_gmail(addr, subject, body)
                        sent_to.append(addr)
                    except Exception as ex:
                        st.error(f"Failed to email {addr}: {ex}")
                if sent_to:
                    st.success(f"Reminder sent to: {', '.join(sent_to)}")

    # ---------- Feedback ----------
    with tabs[4]:
        st.write("### Interview Feedback")
        fb_cand = st.text_input("Candidate Email / Name")
        fb_rating = st.slider("Rating", 1, 5, 3)
        fb_notes = st.text_area("Notes")
        notify_panel = st.text_input("Notify panel email (optional)")
        if st.button("Save Feedback"):
            st.success("Feedback recorded ✅")
            if notify_panel:
                try:
                    send_email_gmail(
                        notify_panel,
                        f"Interview Feedback — {fb_cand}",
                        f"Rating: {fb_rating}/5\n\nNotes:\n{fb_notes}",
                    )
                    st.info("Panel notified by email.")
                except Exception as ex:
                    st.error(f"Email failed: {ex}")

# ====================================================
# 4) Post-Offer Candidate Connect
# ====================================================
elif choice == "🤝 Post-Offer Candidate Connect":
    st.subheader("🤝 Post-Offer Candidate Connect (Gmail + Calendar)")

    tabs = st.tabs([
        "Candidate Setup",
        "Engagement Timeline",
        "Follow-Ups",
        "Onboarding Material",
        "Check-Ins & Concerns",
    ])

    # ---------- Candidate Setup ----------
    with tabs[0]:
        name = st.text_input("Candidate Name", value=st.session_state.get("po_name", ""))
        email = st.text_input("Candidate Email", value=st.session_state.get("po_email", ""))
        role = st.text_input("Role Offered", value=st.session_state.get("po_role", ""))
        join_date = st.date_input("Joining Date", value=st.session_state.get("po_join", datetime.date.today()))
        if st.button("Save Candidate"):
            st.session_state.update({"po_name": name, "po_email": email, "po_role": role, "po_join": join_date})
            st.success("Candidate saved ✅")

    # ---------- Engagement Timeline ----------
    with tabs[1]:
        if not st.session_state.get("po_join"):
            st.warning("Please complete Candidate Setup first.")
        else:
            jd = st.session_state["po_join"]
            checkpoints = {
                "T-30": jd - datetime.timedelta(days=30),
                "T-15": jd - datetime.timedelta(days=15),
                "T-7": jd - datetime.timedelta(days=7),
                "T-1": jd - datetime.timedelta(days=1),
                "T+7": jd + datetime.timedelta(days=7),
            }
            st.table({"Checkpoint": list(checkpoints.keys()), "Date": list(checkpoints.values())})
            which = st.selectbox("Choose checkpoint", list(checkpoints.keys()))
            if st.button("Generate AI Email"):
                dleft = (jd - datetime.date.today()).days
                draft = generate_ai_email(st.session_state.get("po_name","Candidate"), st.session_state.get("po_role","Role"), dleft)
                st.session_state["po_draft"] = draft
                st.success("Draft generated.")
            st.text_area("Email Draft (editable)", key="po_draft", height=220)
            if st.button("Send This Email"):
                try:
                    send_email_gmail(
                        st.session_state.get("po_email",""),
                        f"[JadeHire] Engagement — {which}",
                        st.session_state.get("po_draft",""),
                    )
                    st.success("Email sent ✅")
                except Exception as ex:
                    st.error(f"Email failed: {ex}")

    # ---------- Follow-Ups ----------
    with tabs[2]:
        msg = st.text_area("Compose Follow-Up Message", "Hi, just checking in. Let us know if you need anything!")
        if st.button("Send Follow-Up"):
            try:
                send_email_gmail(st.session_state.get("po_email",""), f"Follow-Up: {st.session_state.get('po_role','')}", msg)
                st.success("Follow-up sent ✅")
            except Exception as ex:
                st.error(f"Email failed: {ex}")

    # ---------- Onboarding Material ----------
    with tabs[3]:
        st.caption("Upload onboarding docs (names kept in session for reference).")
        files = st.file_uploader("Upload files", accept_multiple_files=True)
        if files:
            st.session_state.setdefault("po_files", [])
            for f in files:
                st.session_state["po_files"].append(f.name)
            st.success(f"Stored file names: {', '.join(f.name for f in files)}")
        st.write("Current files:", st.session_state.get("po_files", []))

    # ---------- Check-Ins & Concerns ----------
    with tabs[4]:
        st.write("#### Schedule Check-In (Calendar)")
        c_date = st.date_input("Check-In Date", datetime.date.today() + datetime.timedelta(days=7))
        c_time = st.time_input("Check-In Time", datetime.time(11, 0))
        c_body = st.text_area("Check-In Notes", "Quick touchpoint before Day 1.")
        if st.button("Create Check-In Event"):
            try:
                cal = get_google_service("calendar", "v3")
                start = datetime.datetime.combine(c_date, c_time)
                end = start + datetime.timedelta(minutes=30)
                ev = {
                    "summary": f"Check-In: {st.session_state.get('po_name','Candidate')}",
                    "description": c_body,
                    "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
                    "end": {"dateTime": end.isoformat(), "timeZone": TIMEZONE},
                    "attendees": [{"email": st.session_state.get("po_email","")}],
                }
                created = cal.events().insert(calendarId="primary", body=ev, sendUpdates="all").execute()
                st.success(f"Check-in scheduled ✅  →  {created.get('htmlLink')}")
            except Exception as ex:
                st.error(f"Calendar error: {ex}")

        st.write("#### Concerns / Questions")
        concern = st.text_area("Log candidate concern", "")
        if st.button("Save Concern"):
            st.session_state.setdefault("po_concerns", [])
            if concern.strip():
                st.session_state["po_concerns"].append(
                    {"when": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'), "text": concern.strip()}
                )
                st.success("Concern saved.")
        if st.session_state.get("po_concerns"):
            st.write("Saved concerns:")
            for c in st.session_state["po_concerns"]:
                st.write(f"- [{c['when']}] {c['text']}")
# ====================================================
# 5) LLM Utilization
# ====================================================
elif choice == "🧠 LLM Utilization":
    st.subheader("🧠 LLM Utilization & Quota Tracking")

    calls = st.session_state.get("llm_calls", 0)
    in_tokens = st.session_state.get("llm_in_tokens", 0)
    out_tokens = st.session_state.get("llm_out_tokens", 0)
    total_tokens = in_tokens + out_tokens

    col1, col2, col3 = st.columns(3)
    col1.metric("LLM API Calls", calls)
    col2.metric("Input Tokens (approx)", in_tokens)
    col3.metric("Output Tokens (approx)", out_tokens)

    st.metric("Total Tokens (approx)", total_tokens)

    st.markdown("---")
    st.write("### Provider Quota")
    st.info("Gemini currently does not expose usage via API. Check your Google AI Studio / GCP console for exact quota.")
    st.markdown("- [Gemini Console](https://aistudio.google.com/app/apikey)")



