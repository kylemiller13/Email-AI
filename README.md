# Email Risk AI — Phishing Detection System

A full-stack phishing detection prototype using React, FastAPI, scikit-learn, Gmail API, and SQLite.

---

## Quick Start

### 1. Prerequisites
- Python 3.9+
- Node.js 18+
- Google Cloud Console credentials (Gmail API + OAuth 2.0)

### 2. Setup

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..

# Environment variables
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET in .env

# Train the model (required before first run)
python3 -m ml.train
```

### 3. Run

**Terminal 1 — FastAPI backend:**
```bash
uvicorn api.main:app --reload --port 9000
```

**Terminal 2 — React frontend:**
```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` and sign in with Google.

### 4. Test Without Gmail (Optional)

```bash
python3 -m tests.simulate_phishing
```

Posts 3 phishing + 2 legitimate test emails to the API and prints results.

---

## Project Structure

```
email-risk-ai/
├── frontend/                      # React + Chakra UI
│   └── src/
│       ├── App.tsx                # App shell, auth, nav
│       ├── pages/
│       │   ├── Dashboard.tsx      # Email list and risk tabs
│       │   ├── Admin.tsx          # Metrics, feedback, retrain
│       │   └── SignIn.tsx         # Google OAuth sign-in
│       └── components/
│           ├── EmailCard.tsx
│           └── EmailDetailModal.tsx
├── api/                           # FastAPI backend
│   ├── main.py
│   └── routes/
│       ├── emails.py
│       ├── feedback.py
│       ├── admin.py
│       └── oauth.py
├── ml/                            # Machine learning
│   ├── features.py                # Engineered feature extraction
│   ├── train.py                   # Training script
│   ├── predict.py                 # Inference
│   ├── model.pkl                  # Trained model (generated)
│   └── dataset/                   # CSV training data
├── db/
│   ├── database.py
│   └── schema.sql
├── tests/
│   └── simulate_phishing.py
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/emails/scan` | Analyze an email |
| `GET` | `/emails?user_email=` | Get all analyzed emails for a user |
| `GET` | `/emails/{id}` | Get a specific email |
| `POST` | `/feedback` | Submit a correction |
| `GET` | `/admin/metrics?user_email=` | Detection metrics |
| `GET` | `/admin/feedback?user_email=` | False positive/negative log |
| `POST` | `/admin/retrain` | Retrain model |
| `GET` | `/oauth/authorize` | Get Google OAuth URL |
| `POST` | `/oauth/token` | Exchange code for token |
| `GET` | `/health` | API status |

Full interactive docs: `http://localhost:9000/docs`

---

## Model Details

- **Features:** 22 engineered features (URL, sender, content, structural) + 1000 TF-IDF features
- **Classifier:** Logistic Regression
- **Risk levels:** `critical` (≥85% confidence), `warning` (≥50%), `safe` (<50%)
- **Warning signs:** Human-readable labels for fired features

---

## Troubleshooting

**Port in use:**
```bash
lsof -ti:9000 | xargs kill
lsof -ti:5173 | xargs kill
```

**Model not found:**
```bash
python3 -m ml.train
```

**Database reset:**
```bash
rm db/emails.db
# Reinitializes automatically on next API start
```

**Google OAuth issues:**
- Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`
- Redirect URI in Google Console must be `http://localhost:9000/oauth/callback`
- Gmail API must be enabled in Google Cloud Console
