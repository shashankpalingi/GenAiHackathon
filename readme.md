# 📸 Drishyamitra — AI-Powered Photo Management System

> Transform your photo chaos into an intelligent, organized memory archive using AI-driven face recognition and a conversational chatbot.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![React](https://img.shields.io/badge/React.js-18-61DAFB)
![DeepFace](https://img.shields.io/badge/DeepFace-Facenet512-orange)
![Groq](https://img.shields.io/badge/Groq-Llama3.3_70B-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 About The Project

Drishyamitra is an intelligent photo management system that combines deep learning-based facial recognition with a conversational AI chatbot to automate how you organize, search, and share your memories.

Unlike traditional photo galleries that rely on manual sorting, Drishyamitra automatically detects faces, groups photos by person, and enables natural language commands like:

- _"Show me photos of Priya from last month"_
- _"Send John's pictures to WhatsApp"_
- _"Email Mom her birthday photos from last year"_

---

## ✨ Features

- 🤖 **AI Face Recognition** — Detects and identifies faces using DeepFace (Facenet512, RetinaFace, MTCNN)
- 💬 **Conversational Chatbot** — Natural language photo queries powered by Groq API (Llama 3.3 70B)
- 📂 **Smart Organization** — Auto-groups photos into person-specific folders
- 📧 **Email Delivery** — Send photos directly via Gmail with one command
- 📱 **WhatsApp Sharing** — Deliver photos to WhatsApp contacts instantly
- 🔐 **Secure Auth** — JWT-based authentication with bcrypt password hashing
- 📊 **Delivery History** — Tracks all email/WhatsApp delivery logs
- 🖥️ **Responsive UI** — Clean dashboard built with React.js and Tailwind CSS

---

## 🛠️ Tech Stack

| Layer            | Technology                               |
| ---------------- | ---------------------------------------- |
| Backend          | Flask (Python 3.8+)                      |
| Frontend         | React.js + Tailwind CSS                  |
| Face Recognition | DeepFace (Facenet512, RetinaFace, MTCNN) |
| AI Chatbot       | Groq API — Llama 3.3 70B / Mixtral 8x7B  |
| Database         | SQLite (dev) / PostgreSQL (prod)         |
| ORM              | SQLAlchemy                               |
| Authentication   | Flask-JWT-Extended + bcrypt              |
| Email            | Gmail API + SMTP                         |
| WhatsApp         | whatsapp-web.js / PyWhatKit              |
| Deployment       | Docker Compose + Nginx + SSL             |

---

## 🗂️ Project Structure

```
Drishyamitra/
├── backend/
│   ├── models/          # SQLAlchemy ORM models
│   ├── routes/          # Flask blueprints (auth, chat, photos, delivery, face)
│   ├── services/        # FaceRecognitionService, AIAssistant, GmailService, WhatsAppService
│   ├── data/            # photos, faces, embeddings, zips
│   ├── app.py           # Flask app factory
│   ├── config.py        # Configuration
│   ├── start_server.py  # Entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # Axios API calls
│   │   └── utils/       # Helpers
│   ├── public/
│   └── package.json
└── docker-compose.yml
```

---

## ⚙️ Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.8+
- Node.js 16+ (includes npm 8+)
- Git

And the following API credentials ready:

- [Groq API Key](https://console.groq.com/keys)
- Gmail App Password ([Generate here](https://myaccount.google.com/apppasswords))
- Google Cloud OAuth credentials (for Gmail API)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/drishyamitra.git
cd drishyamitra
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Backend Environment

Create a `.env` file inside the `backend/` folder:

```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key
DEBUG=False

# Groq API
GROQ_API_KEY=your-groq-api-key

# Google / Gmail
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
GMAIL_EMAIL=your-email@gmail.com
GMAIL_PASSWORD=your-app-password

# Database
DATABASE_URL=sqlite:///database/drishyamitra.db

# File Storage
UPLOAD_FOLDER=data/photos
TEMP_FOLDER=data/temp
EMBEDDINGS_FOLDER=data/embeddings
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,heic

# WhatsApp
WHATSAPP_API_URL=http://localhost:3001

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
```

### 4. Start the Backend

```bash
python start_server.py
```

Backend runs at: `http://localhost:5000`

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

Create a `.env` file inside the `frontend/` folder:

```env
REACT_APP_API_URL=http://localhost:5000
```

### 6. Start the Frontend

```bash
npm start
```

Frontend runs at: `http://localhost:3000`

---

## 🗄️ Database Models

| Model             | Description                          |
| ----------------- | ------------------------------------ |
| `User`            | Stores user credentials and profile  |
| `Photo`           | Image metadata and file paths        |
| `Face`            | Detected face crops with embeddings  |
| `Person`          | Named identities linked to faces     |
| `DeliveryHistory` | Log of all email/WhatsApp deliveries |

---

## 🔌 API Endpoints

| Method | Endpoint                 | Description                |
| ------ | ------------------------ | -------------------------- |
| POST   | `/api/auth/register`     | Register new user          |
| POST   | `/api/auth/login`        | Login and receive JWT      |
| POST   | `/api/photos/upload`     | Upload photos              |
| GET    | `/api/photos/`           | List all user photos       |
| POST   | `/api/face/label`        | Label a detected face      |
| GET    | `/api/face/recognize`    | Run recognition on photo   |
| POST   | `/api/chat/message`      | Send message to AI chatbot |
| POST   | `/api/delivery/email`    | Send photos via email      |
| POST   | `/api/delivery/whatsapp` | Send photos via WhatsApp   |
| GET    | `/api/history/`          | Get delivery history       |

---

## 💬 Chatbot Commands

You can type natural language commands in the chat interface:

```
"Show me photos of Priya"
"Send Priya's photos to john@example.com"
"Show all photos from last week"
"Send family photos to WhatsApp"
"How many photos do I have of Rahul?"
```

---

## 🧠 AI Models Used

| Model             | Role                                           |
| ----------------- | ---------------------------------------------- |
| **Facenet512**    | Generates face embeddings for recognition      |
| **RetinaFace**    | Robust face detection under various conditions |
| **MTCNN**         | Face alignment and landmark extraction         |
| **Llama 3.3 70B** | Powers the conversational chatbot via Groq     |

> DeepFace models download automatically on first run (~500MB). Ensure a stable internet connection initially.

---

## 📱 Application Screenshots

| Page         | Description                              |
| ------------ | ---------------------------------------- |
| 🏠 Home      | Landing page with Get Started CTA        |
| 🔐 Auth      | Login and Signup forms                   |
| 📊 Dashboard | Stats overview + Quick Upload            |
| 🖼️ Gallery   | Photo grid with face labeling modal      |
| 💬 Chat      | AI chatbot interface with photo previews |
| 📜 History   | Delivery log with timestamps             |

---

## 🐳 Docker Deployment (Production)

```bash
# Build and start all services
docker-compose up --build

# Stop all services
docker-compose down
```

The `docker-compose.yml` spins up:

- Flask backend
- React frontend
- PostgreSQL database
- Nginx reverse proxy (with SSL)

---

## 👥 Team & Branch Structure

| Collaborator   | Branch                    | Responsibility                              |
| -------------- | ------------------------- | ------------------------------------------- |
| Collaborator 1 | `feat/backend-core`       | Flask setup, Auth, DB models                |
| Collaborator 2 | `feat/face-ai`            | DeepFace integration, Recognition service   |
| Collaborator 3 | `feat/frontend`           | React UI, Gallery, Upload, Dashboard        |
| Collaborator 4 | `feat/chatbot-email`      | Groq chatbot, Gmail, WhatsApp delivery      |
| Collaborator 5 | `feat/integration-polish` | Testing, Docker, Deployment, Git management |

### Git Workflow

```bash
# Start work
git checkout dev && git pull origin dev
git checkout feat/your-branch
git merge dev

# Commit often
git add .
git commit -m "feat: add face embedding storage"
git push origin feat/your-branch

# Merge checkpoint (open PR to dev)
```

**Commit convention:** `feat:` `fix:` `chore:` `test:` `docs:` `refactor:`

---

## 🔒 Security

- All passwords hashed with **bcrypt**
- API routes protected with **JWT tokens**
- Sensitive credentials stored in `.env` (never committed)
- Gmail uses **OAuth 2.0** — no plain-text passwords
- Face embeddings stored encrypted in the database

---

## 🚧 Known Limitations

- WhatsApp Web API requires phone to be connected during session
- DeepFace recognition accuracy depends on photo quality and lighting
- First run requires ~500MB model download for DeepFace
- Bulk uploads of 100+ photos may take time due to embedding generation

---

## 🔮 Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Cloud storage integration (Google Drive, S3)
- [ ] Emotion detection in photos
- [ ] Location-based photo tagging
- [ ] Multi-language chatbot support
- [ ] Real-time face recognition via webcam

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [DeepFace](https://github.com/serengil/deepface) by Sefik Ilkin Serengil
- [Groq](https://groq.com/) for lightning-fast LLM inference
- [SmartBridge](https://smartbridge.com/) & SkillWallet for project guidance
- Flask, React.js, and Tailwind CSS open source communities

---
