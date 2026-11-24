# Enterprise AI Customer Support & E-Commerce Assistant

This project is a small e-commerce support application that brings customer and order lookups together with an AI-powered document assistant.

I built it to explore how RAG, SQL queries and APIs can work together in one application.

The application includes:

- An AI assistant that answers questions using uploaded documents such as FAQs, return policies and shipping policies.
- Customer, order, product, inventory and support ticket lookups using SQL.
- A basic business dashboard with order and inventory information.
- Document upload and ingestion for PDF, DOCX, TXT, CSV and Excel files.
- A FastAPI backend and Streamlit frontend.
- JWT-based authentication for the demo login.

## Technologies used

- Python
- FastAPI
- Streamlit
- SQLite
- SQLAlchemy
- Ollama (`qwen2.5:3b`)
- RAG (Retrieval-Augmented Generation)
- JWT authentication

## How the application works

The application handles different types of questions through different paths:

1. Questions about customers, orders, products, inventory and tickets are handled using database queries.
2. Business-related questions are handled by the reporting logic.
3. Questions about policies, FAQs and uploaded documents go through the RAG pipeline. Relevant document content is retrieved and passed to Ollama to generate an answer.

The application uses local hashed-token vectors and lexical matching for document retrieval. Ollama is used to generate answers from the retrieved content.

## Requirements

- Windows 10 or 11
- Python 3.14
- Git (optional, for cloning the repository)
- Ollama installed
- Internet connection for the initial package installation

The application uses a local Ollama model, so an OpenAI API key is not required.

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/manoj9945/Enterprise-rag-customer-support-assistant.git
cd Enterprise-rag-customer-support-assistant
```

### 2. Install and prepare Ollama

Download and install Ollama from:

https://ollama.com/

Open PowerShell and download the model:

```powershell
ollama pull qwen2.5:3b
```

Make sure Ollama is running before starting the application.

### 3. Start the application

Run this command from the project folder:

```powershell
.\run_project.bat
```

The startup script creates the Python virtual environment if needed, installs the required packages and starts the backend and frontend.

### 4. Open the application

Open this address in your browser:

http://localhost:8501

Use the following demo credentials:

- Username: `admin`
- Password: `admin123`

The database is created and sample records are added during the initial setup.

## Manual setup

If you prefer to start the services separately, follow these steps.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Start the FastAPI backend:

```powershell
uvicorn backend.main:app --reload
```

Open another PowerShell window, navigate to the project folder, activate the virtual environment and start Streamlit:

```powershell
streamlit run frontend/app.py
```

The application will be available at:

- Frontend: http://localhost:8501
- API: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs

## Example questions to try

**Customer and order queries**

- How many customers are there?
- Show me all orders and their statuses.
- Where is order 3?

**Inventory queries**

- Show current inventory.
- Which products have low stock?

**Business reports**

- Show sales report.
- What is the total revenue?

**Document-based questions**

- What is your return policy?
- How long does delivery take?
- How do I report a damaged item?

You can also upload your own supported documents and ask questions about their content.

## Project structure

```text
Enterprise_RAG_Assistant/
│
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── rag.py
│   ├── security.py
│   ├── seed.py
│   └── services.py
│
├── frontend/
│   └── app.py
│
├── data/
│   └── documents/
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── INTERVIEW_GUIDE.md
│
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── run_project.bat
```

## Current limitations

This is a learning and demonstration project, not a production-ready enterprise application.

A few things to keep in mind:

- The question router uses Python keyword rules rather than an autonomous AI agent.
- Document retrieval uses local hashed-token vectors and lexical matching. It does not use a dedicated neural embedding model or an external vector database.
- The reporting functionality currently provides a basic operational snapshot.
- The application keeps conversation messages in the Streamlit session. Persistent conversational memory is not implemented.
- Authentication uses a demo admin account. A production application would need a proper user management system, stronger role-based access control and additional security measures.
- Uploaded documents are stored locally in the `data/documents` folder.
- The sample customer, order and product records are synthetic.

Change the default demo password and JWT secret before using the application in any shared environment.

## Running tests

Activate the virtual environment and run:

```powershell
python -m pytest -q
```

## Troubleshooting

- If the application cannot connect to Ollama, check whether Ollama is running.
- If the model is missing, run `ollama pull qwen2.5:3b`.
- If the frontend cannot connect to the backend, make sure the FastAPI server is running.
- If a Python package fails to install, check the Python version and the installation error.
- If ports 8000 or 8501 are already in use, stop the process using the port before restarting the application.
