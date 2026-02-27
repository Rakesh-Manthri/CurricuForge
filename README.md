# 🛠️ CurricuForge: Generative AI–Powered Curriculum Design System

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)
![Framework](https://img.shields.io/badge/framework-FastAPI-009688.svg)
![AI Model](https://img.shields.io/badge/AI_Model-IBM_Granite_3.3_2B-orange.svg)

**CurricuForge** is an intelligent curriculum design platform that leverages IBM's **Granite 3.3 2B** AI model (via Ollama) to provides comprehensive educational curriculum generation and planning recommendations.

---

## 🌟 Key Features

- **AI-Powered Analysis**: Uses Granite 3.3 2B's advanced language capabilities to analyze educational parameters.
- **Tailored Curriculum**: Generates accurate course names, learning topics, and descriptions based on skill, education level, industry focus, and more.
- **Local Inference**: Fast response times and privacy through local **Ollama** deployment—no cloud API keys required.
- **Modern Interface**: A user-friendly, responsive frontend with smooth animations and dynamic design.
- **PDF Generation**: Export professional curriculum documents using ReportLab.
- **Personalized Guidance**: Considers skill complexity, learning progression, and industry relevance for every generated syllabus.

---

## 🚀 Core Technologies
- **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
- **IBM Granite 3.3 2B**: State-of-the-art local AI model for intelligent generation.
- **HTML5/CSS3/JavaScript**: Modern frontend with a focus on UX and responsiveness.
- **ReportLab**: Integration for professional PDF document generation.
- **Python Algorithms**: Sophisticated logic for curriculum structure and validation.

---

## 📋 Prerequisites

### Software Requirements
- **Python 3.8+**: [Download here](https://www.python.org/)
- **Ollama**: [Download here](https://ollama.ai/)
- **Git**: [Download here](https://git-scm.com/)
- **Granite 3.3 2B Model**: Pre-downloaded via Ollama:
  ```bash
  ollama pull granite3.3:2b
  ```

### Hardware Requirements
- **Processor**: Intel i5/AMD Ryzen 5 or better.
- **RAM**: 8GB Minimum (16GB recommended for smooth Ollama performance).
- **Storage**: 10GB free space (primarily for the AI model).

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
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure Ollama is Running**
   Make sure the Ollama service is active and the `granite:3.3-2b` model is downloaded.

5. **Run the Application**
   ```bash
   uvicorn app:app --reload
   ```
<<<<<<< HEAD
   Access the platform at `http://127.0.0.1:8000`.
=======
   Access the platform at `http://127.0.0.1:5001`.
>>>>>>> 7985ae0d17c47dc108dc870aa9bc1cbf771b2d41

---

## 📂 Project Structure
```text
CurricuForge/
├── static/             # CSS, JS, and image assets
├── templates/          # HTML templates
├── app.py              # Main Flask application
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License.
