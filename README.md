# 🛠️ CurricuForge: AI-Powered Curriculum Design Platform

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)
![Framework](https://img.shields.io/badge/framework-FastAPI-009688.svg)
![AI Model](https://img.shields.io/badge/AI_Model-IBM_Granite_3.3_2B-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**CurricuForge** is an intelligent curriculum design platform that leverages IBM's **Granite 3.3 2B** AI model (via [Ollama](https://ollama.com/)) to generate comprehensive, industry-aligned educational curricula. Everything runs **locally** on your machine — no cloud APIs, no data leaving your system.

---

## 🌟 Key Features

- **🧠 Multi-Agent AI Pipeline**: Uses a Planner → Detailer → Reviewer agentic workflow (via LangGraph) for high-quality curriculum generation.
- **📋 Step-by-Step Generation**: Guided multi-step form (Basics → Learning → Industry) with validation and progressive navigation.
- **🎓 Structured Output**: Semester-wise courses with credits, durations, topics, and detailed descriptions — all parsed into clean, structured data.
- **💬 AI Chat Assistant**: Ask follow-up questions about your generated curriculum with a built-in conversational AI.
- **📄 PDF Export**: Download professional, formatted curriculum documents via ReportLab integration.
- **📁 Generation History**: Browse, revisit, and manage all previously generated curricula (stored in SQLite).
- **📊 Analysis Dashboard**: Visualize trends and insights across your generation history.
- **🔐 Authentication**: User sign-up/sign-in with session-based auth — personalized history per user.
- **📧 Contact Form**: Working email integration via Gmail SMTP — messages from the Contact page are delivered to your inbox.
- **🌙 Dark Mode**: Full site-wide dark/light theme toggle with persistent preference.
- **🔒 100% Local & Private**: All AI inference runs locally via Ollama. No data ever leaves your machine.
- **🔔 Toast Notifications**: Elegant slide-in notifications for success, error, and validation feedback.

---

## 🚀 Core Technologies

| Technology | Purpose |
|---|---|
| [**FastAPI**](https://fastapi.tiangolo.com/) | High-performance Python web framework for APIs and server-rendered pages |
| [**IBM Granite 3.3 2B**](https://ollama.com/library/granite3.3:2b) | State-of-the-art local AI model for intelligent curriculum generation |
| [**Ollama**](https://ollama.com/) | Local LLM runtime enabling fast, private inference |
| **LangGraph + LangChain** | Multi-agent orchestration (Planner, Detailer, Reviewer agents) |
| **HTML5 / CSS3 / JavaScript** | Modern, responsive frontend with glassmorphism and micro-animations |
| **SQLite (aiosqlite)** | Async local database for user accounts, sessions, and curriculum history |
| [**ReportLab**](https://www.reportlab.com/) | Professional PDF document generation |
| **Jinja2** | Server-side HTML templating |

---

## 📋 Prerequisites

### Software Requirements
- **Python 3.8+**: [Download here](https://www.python.org/)
- **Ollama**: [Download here](https://ollama.com/)
- **Git**: [Download here](https://git-scm.com/)
- **Granite 3.3 2B Model**: Pre-downloaded via Ollama:
  ```bash
  ollama pull granite3.3:2b
  ```

### Hardware Requirements
- **Processor**: Intel i5 / AMD Ryzen 5 or better
- **RAM**: 8GB Minimum (16GB recommended for smooth Ollama performance)
- **Storage**: 10GB free space (primarily for the AI model)

---

## 🛠️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Rakesh-Manthri/CurricuForge.git
   cd CurricuForge
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables** *(optional — for Contact form email)*
   
   Create a `.env` file in the project root:
   ```env
   SMTP_EMAIL=your_gmail@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   CONTACT_TO_EMAIL=your_gmail@gmail.com
   ```
   > **Note**: You need a [Gmail App Password](https://myaccount.google.com/apppasswords) (not your regular password). Requires 2-Step Verification to be enabled.

5. **Start Ollama** *(in a separate terminal)*
   ```bash
   ollama serve
   ```
   Make sure the Granite model is pulled:
   ```bash
   ollama pull granite3.3:2b
   ```

6. **Run the Application**
   ```bash
   uvicorn app:app --reload
   ```
   Access the platform at **http://127.0.0.1:8000**

---

## 📂 Project Structure

```text
CurricuForge/
├── static/
│   ├── css/
│   │   └── style.css           # Global styles, themes, dark mode, responsiveness
│   └── js/
│       ├── main.js             # Shared: navbar, theme toggle, notifications, auth
│       ├── generate.js         # Multi-step form, AI generation, chat, PDF export
│       ├── contact.js          # Contact form validation & SMTP submission
│       ├── history.js          # Generation history list & management
│       ├── analysis.js         # Analytics dashboard & visualizations
│       ├── auth.js             # Sign-up/sign-in form handling
│       └── script.js           # Misc shared utilities
├── templates/
│   ├── index.html              # Landing page with hero, features, how-it-works
│   ├── generate.html           # Curriculum generation (multi-step form + output)
│   ├── about.html              # About page with tech stack & mission
│   ├── contact.html            # Contact form with email integration
│   ├── history.html            # Curriculum generation history
│   ├── analysis.html           # Analytics dashboard
│   ├── signin.html             # User sign-in page
│   ├── signup.html             # User sign-up page
│   └── layout.html             # Base layout template
├── app.py                      # FastAPI application — routes, API endpoints, AI logic
├── agents.py                   # LangGraph multi-agent workflow (Planner/Detailer/Reviewer)
├── database.py                 # SQLite async DB — users, sessions, curriculum storage
├── pdf_generator.py            # ReportLab PDF generation logic
├── requirements.txt            # Python dependencies
├── .env                        # SMTP credentials (not committed to git)
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🖥️ Pages & Features

| Page | Route | Description |
|---|---|---|
| **Home** | `/` | Hero section, feature overview, how-it-works, CTA |
| **Generate** | `/generate` | Step-by-step curriculum generator with AI chat & PDF export |
| **About** | `/about` | Project mission, core technologies, team info |
| **Contact** | `/contact` | Contact form with validation & real email delivery |
| **History** | `/history` | Browse & manage previously generated curricula |
| **Analysis** | `/analysis` | Visual analytics of generation patterns & trends |
| **Sign Up** | `/signup` | Create a new account |
| **Sign In** | `/signin` | Log in to your account |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Generate a new curriculum using the AI pipeline |
| `POST` | `/api/contact` | Send a contact form message via email |
| `POST` | `/api/chat` | Chat with the AI about a generated curriculum |
| `POST` | `/api/auth/signup` | Create a new user account |
| `POST` | `/api/auth/signin` | Authenticate and create a session |
| `POST` | `/api/auth/signout` | Sign out and delete session |
| `GET` | `/api/auth/me` | Get current authenticated user |
| `GET` | `/api/curricula` | List curriculum history for the logged-in user |
| `GET` | `/api/curricula/{id}` | Get a specific stored curriculum |
| `POST` | `/export-pdf` | Generate and download a curriculum PDF |

---

## 🎨 Design Highlights

- **Glassmorphism UI** with subtle transparency and blur effects
- **Smooth micro-animations** using CSS transitions and IntersectionObserver
- **Responsive design** that works on desktop, tablet, and mobile
- **Dark/Light theme** toggle with `localStorage` persistence
- **Gradient accents** using a curated indigo → cyan → violet palette
- **Toast notification system** with slide-in animations for success, error, and info states

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 📬 Contact

Have questions or feedback? Reach out at **manthrirs06@gmail.com** or open an issue on [GitHub](https://github.com/Rakesh-Manthri/CurricuForge).

---

<div align="center">
  <strong>Built with ❤️ using IBM Granite 3.3 2B</strong><br>
  <sub>© 2026 CurricuForge. All rights reserved.</sub>
</div>
