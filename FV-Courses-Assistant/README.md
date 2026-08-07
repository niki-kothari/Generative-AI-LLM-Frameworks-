# 🚀 Future Vision Courses Project

A modern **AI-powered Course Management & Intelligent Search System** built with **Python, Streamlit, LangChain, Firebase Firestore, OpenAI Embeddings, and FAISS**.

The application enables educational institutes to upload course materials (PDFs), automatically process and index their content, store structured course metadata, and provide an intelligent semantic search experience powered by Large Language Models (LLMs).

---

## 📌 Overview

The Future Vision Courses Project transforms traditional course catalogs into an AI-powered knowledge base.

When a course PDF is uploaded, the system:

* Extracts text from the document
* Splits the content into semantic chunks
* Generates vector embeddings using OpenAI
* Stores embeddings in a FAISS vector database
* Stores metadata and document chunks in Firebase Firestore
* Enables natural language course search using Retrieval-Augmented Generation (RAG)

This provides users with a fast, intelligent, and context-aware course discovery experience.

---

# ✨ Features

## 📚 Course Management

* Upload course PDFs
* Create, update, list, and delete courses
* Manage course categories
* Store course metadata
* Automatic keyword extraction
* Tool and technology tagging

---

## 🤖 AI & Semantic Search

* OpenAI Embeddings
* FAISS Vector Database
* Semantic similarity search
* Hybrid retrieval strategy
* Context-aware question answering
* Metadata-based ranking
* Keyword-enhanced retrieval

---

## ☁️ Firebase Integration

* Firestore database
* Auto-generated Course IDs
* Course metadata storage
* Document chunk storage
* Category management

---

## 📄 PDF Processing

* PDF ingestion
* Automatic text extraction
* Recursive document chunking
* Intelligent preprocessing
* Lemmatization
* Stop-word removal

---

## 🖥 User Interface

* Streamlit dashboard
* Interactive course management
* AI search interface
* Category management
* Course listing
* Update/Delete operations

---

# 🏗 Project Architecture

```text
                    Course PDF
                         │
                         ▼
               PDF Text Extraction
                         │
                         ▼
              Recursive Text Chunking
                         │
                         ▼
            OpenAI Embedding Generation
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   FAISS Vector Index            Firebase Firestore
 (Semantic Search)          (Metadata + Chunks + Categories)
          │                             │
          └──────────────┬──────────────┘
                         ▼
                 Hybrid Retrieval Engine
                         │
                         ▼
                 AI Course Assistant
                         │
                         ▼
                 Natural Language Answer
```

---

# 📂 Project Structure

```text
FV-Courses-Project/
│
├── data/
│   ├── faiss_index/              # FAISS vector index
│   └── pdfs/                     # Uploaded course PDFs
│
├── store_pdf.py                  # PDF ingestion pipeline
├── retrieve_data.py              # Search & retrieval engine
├── category_form.py              # Category management
├── firebase_config.py            # Firebase configuration
├── future_vision_firebase_key.json
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Technology Stack

| Category         | Technologies       |
| ---------------- | ------------------ |
| Language         | Python             |
| UI               | Streamlit          |
| AI Framework     | LangChain          |
| Embeddings       | OpenAI Embeddings  |
| Vector Database  | FAISS              |
| Database         | Firebase Firestore |
| PDF Processing   | PyMuPDF            |
| NLP              | NLTK               |
| Machine Learning | Scikit-learn       |
| Environment      | python-dotenv      |

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/FV-Courses-Project.git
cd FV-Courses-Project
```

---

## 2. Create a Virtual Environment

### Windows PowerShell

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bash
.venv\Scripts\activate.bat
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=your_openai_api_key
```

---

## 5. Configure Firebase

Place your Firebase Service Account JSON file in the project root.

```text
future_vision_firebase_key.json
```

---

## 6. Run the Application

```bash
streamlit run store_pdf.py
```

---

# 📖 How It Works

## Step 1 — Add a Course

* Upload a course PDF
* Enter metadata
* Select category
* Enter tools used
* Store the course

The system automatically:

* extracts text
* creates chunks
* generates embeddings
* stores vectors
* stores metadata
* extracts keywords

---

## Step 2 — Ask Questions

Users can ask questions like:

> Which course teaches LangChain?

> I want to learn Python for AI.

> Recommend a beginner AI course.

The system retrieves the most relevant course content and generates intelligent responses using semantic search.

---

## Step 3 — Manage Courses

Available operations include:

* List Courses
* Update Courses
* Delete Courses
* Manage Categories

---

# 🧠 AI Pipeline

```text
PDF
 │
 ▼
PyMuPDF
 │
 ▼
Text Chunking
 │
 ▼
OpenAI Embeddings
 │
 ▼
FAISS
 │
 ▼
Hybrid Retrieval
 │
 ▼
LLM Response
```

---

# 🔒 Security

* Keep Firebase credentials private.
* Never commit `.env` or service account keys to Git.
* Store API keys securely.
* Restrict Firestore permissions in production.
* Use GitHub Secrets for deployment.

---

# 📌 Future Enhancements

* User authentication
* Multi-user roles
* Admin dashboard
* Course recommendation engine
* Course similarity search
* Analytics dashboard
* REST API
* FastAPI backend
* LangGraph workflow integration
* RAG evaluation metrics
* Multi-LLM support
* Cloud deployment
* Vector database migration (Pinecone, Qdrant, Chroma)
* Conversation history
* Course recommendation chatbot

---

# 📄 License

This project is intended for educational and research purposes. Add an appropriate open-source license (such as MIT or Apache 2.0) if you plan to distribute it publicly.

---

# 👨‍💻 Author

**Future Vision Computer Institute**

AI-Powered Educational Solutions using Python, LangChain, LLMs, Firebase, FAISS, and Streamlit.

---

⭐ If you find this project useful, consider giving the repository a **Star** on GitHub.
