
# JadeHire — AI-Powered Talent Acquisition Platform 💼

## 🔹 Overview
JadeHire is an AI-driven Talent Acquisition platform built on **Google Gemini LLM (gemini-2.5-flash)** with seamless integration to **Google Calendar API** and **Gmail API**.  
It transforms recruitment by automating resume screening, standardization, interview scheduling, post-offer candidate engagement, and tracking LLM utilization.

---

## 🔧 Technology Stack
- **LLM**: Google Gemini (gemini-2.5-flash)
- **APIs**: Google Calendar API & Gmail API
- **Framework**: Streamlit (Python)
- **Other Packages**: `google-auth-oauthlib`, `google-api-python-client`, `python-docx`, `PyPDF2`, `matplotlib`, `python-dotenv`

---

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/deepalikumbhar-dk/my_first_repo.git
cd my_first_repo/TalentAcquisition
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Setup Google Cloud APIs
- Create a project in [Google Cloud Console](https://console.cloud.google.com)
- Enable **Calendar API** and **Gmail API**
- Create **OAuth Client ID (Desktop app)** credentials
- Download `client_secret.json` into project root

---

## 🚀 Running the App
```bash
streamlit run TalentAcquisition_JadeHire.py
```
- First run → prompts Google login → generates `token.pickle`
- App launches in your browser

---

## 📌 Features (Modules)

### 1️⃣ Resume Screening
- Upload JD + resumes (.docx/.pdf)
- AI recruiter gives **% match** + strengths & gaps
- Visual bar chart ranking candidates

### 2️⃣ Resume Standardization
- Convert resumes into **Jade Global template**
- Output downloadable as **PDF/DOCX**

### 3️⃣ Scheduling & Coordination
- Natural text scheduling → AI extracts details
- Creates calendar invites, reschedules interviews, sends reminders, records feedback

### 4️⃣ Post-Offer Candidate Connect
- Keeps candidates engaged until Day 1
- Engagement timeline (T-30, T-15, T-7, T+7)
- Automated AI follow-ups, onboarding materials, check-ins, and concerns tracking

### 5️⃣ LLM Utilization
- Track **API calls** and **approx token usage**
- Link to Google AI Studio for actual quota details

---

## 🎯 Business Value
- **70% less manual recruiter effort**
- **30% fewer candidate dropouts**
- **Professional branded resumes**
- **Transparent AI cost tracking**

---

## 📂 Project Structure
```
jadehire/
│── TalentAcquisition_JadeHire.py       # Streamlit unified app (all modules)
│── client_secret_deep_personal.json    # Google OAuth credentials
│── .env                                # API keys
│── requirements.txt                    # Python dependencies
│── README.md                           # Documentation
```

---

## 📌 Requirements
- Python 3.9+
- Google Gemini API key
- Google Cloud project with Calendar + Gmail APIs enabled

---

## 🏢 Branding
- JadeHire is designed with **Jade Global branding**
- Sidebar tagline: *Delivering Innovation, Driving Impact™*
- Jade Global logo embedded in sidebar

---

## 📜 License
This project is for **educational and internal demo purposes** only.

---

## 🚀 Closing Note
JadeHire combines **AI intelligence** with **automation** to make hiring smarter, faster, and more engaging.
