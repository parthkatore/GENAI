🤖 ArduinoMate – AI-Powered Arduino Learning Assistant

<p align="center">
<b>Your Personal AI Assistant for Learning Arduino Programming and Electronics.</b>
</p>

1. Introduction

ArduinoMate is an AI-powered learning assistant designed to help beginners, students, and electronics enthusiasts understand Arduino programming and hardware concepts.

Learning Arduino can be challenging because users need to understand programming functions, electronic components, pin configurations, board-specific features, and circuit connections.

ArduinoMate solves this problem by providing an intelligent assistant that answers Arduino-related questions using official Arduino documentation.

Instead of depending entirely on general AI knowledge, ArduinoMate retrieves relevant information from its knowledge base and generates answers with supporting source citations.

The system also includes an AI agent that can use tools such as Arduino documentation search and an LED resistor calculator.

2. Problem Statement

Arduino beginners commonly face these challenges:

Difficulty understanding Arduino programming functions.
Confusion about function syntax, parameters, and return values.
Difficulty understanding digital and analog input/output.
Confusion between Arduino Uno, Nano, and ESP32 capabilities.
Time-consuming searches through technical documentation.
Incorrect or incomplete answers from general-purpose AI tools.
Difficulty calculating resistor values for LED circuits.
Lack of beginner-friendly explanations with trusted references.
Proposed Solution

ArduinoMate provides a centralized AI-powered platform where users can ask questions in natural language and receive understandable answers based on official Arduino documentation.

The system uses Retrieval-Augmented Generation (RAG), semantic search, and AI agents to provide relevant and source-supported information.

3. Objectives

The main objectives are:

Build a structured Arduino documentation knowledge base.
Collect and process Arduino programming reference documents.
Develop keyword-based and semantic search.
Implement an AI-powered question-answering system.
Use RAG to generate answers grounded in retrieved documentation.
Provide citations for technical answers.
Develop an LED resistor calculator using Ohm's law.
Build an AI agent that can select appropriate tools.
Create an interactive Streamlit user interface.
Support board-specific Arduino information.
Evaluate answer quality and retrieval accuracy.
Deploy the application as an accessible web service.
4. Target Users

ArduinoMate is designed for:

Students learning Arduino programming.
Engineering and diploma students.
Beginners in embedded systems.
IoT developers.
Electronics hobbyists.
Teachers and instructors.
Developers working with Arduino-compatible boards.
5. Key Features
5.1 Arduino Documentation Knowledge Base

ArduinoMate collects and processes official Arduino documentation.

The initial knowledge base includes 20 Arduino language functions:

Function	Category
pinMode()	Digital I/O
digitalRead()	Digital I/O
digitalWrite()	Digital I/O
analogRead()	Analog I/O
analogWrite()	Analog I/O
analogReference()	Analog I/O
delay()	Time
delayMicroseconds()	Time
millis()	Time
micros()	Time
map()	Math
constrain()	Math
tone()	Advanced I/O
noTone()	Advanced I/O
pulseIn()	Advanced I/O
Serial.begin()	Serial Communication
Serial.print()	Serial Communication
Serial.read()	Serial Communication
attachInterrupt()	External Interrupts
random()	Random Numbers

Each documentation record contains:

Function name.
Category.
Syntax.
Return information.
Common gotcha.
Source URL.
5.2 Intelligent Search

Users can search Arduino functions using keywords.

Examples:

Search for digital input.
Find PWM functions.
Search for serial communication.
Find functions related to timing.
Search for analog input.

ArduinoMate supports keyword-based search, TF-IDF ranking, and semantic search.

5.3 AI Question Answering

Users can ask Arduino questions in natural language.

Example questions:

What is the difference between digitalRead() and analogRead()?
How does pinMode() work?
Explain the millis() function.
How can I control LED brightness?
What is PWM in Arduino?
How does Serial.begin() work?

The system retrieves relevant documentation and uses an LLM to generate an understandable answer.

5.4 Retrieval-Augmented Generation (RAG)

ArduinoMate uses RAG to improve answer relevance and reduce unsupported responses.

The RAG process:

User enters a question.
The question is converted into an embedding.
Relevant documentation chunks are retrieved.
Retrieved information is passed to the language model.
The model generates an answer using the available context.
Source citations are returned with the answer.
5.5 LED Resistor Calculator

ArduinoMate includes an AI agent tool called led_resistor_calculator.

It calculates an appropriate resistor value using Ohm's law.

Formula:

𝑅
=
𝑉
𝑠
−
𝑉
𝑓
𝐼

Where:

𝑅
 = Required resistance in ohms.
𝑉
𝑠
 = Supply voltage.
𝑉
𝑓
 = LED forward voltage.
𝐼
 = LED current in amperes.

Example:

Supply voltage = 5V
LED forward voltage = 2V
LED current = 0.02A

Calculation:

𝑅
=
5
−
2
0.02
𝑅
=
150
 
Ω

The selected resistor is 150Ω.

The calculator rounds the calculated resistance up to the next standard E12 resistor value.

5.6 Board-Specific Knowledge

ArduinoMate considers hardware differences between Arduino-compatible boards.

Board	Important considerations
Arduino Uno	10-bit ADC and specific PWM pins
Arduino Nano	Capabilities depend on the particular Nano variant
ESP32	ADC resolution, PWM implementation, and voltage characteristics differ

The system aims to provide board-specific explanations instead of assuming that every board behaves identically.

5.7 Arduino Pin Map Visualization

The Streamlit interface includes an interactive Arduino Uno pin map.

It highlights pins mentioned in the generated answer:

Digital pins.
PWM pins marked with ~.
Analog pins A0–A5.

This feature helps beginners understand which pins are involved in a particular Arduino project.

5.8 AI Agent

ArduinoMate includes an AI agent that can select and execute different tools.

Available tools:

Arduino documentation search.
LED resistor calculator.
Board-specific information retrieval.

The agent selects an appropriate tool based on the user's question and generates a final response using the tool results.

6. System Architecture

ArduinoMate follows a modular architecture that separates data collection, processing, retrieval, AI generation, and user interaction.

High-Level Architecture
mermaid
flowchart TD
    A[User] --> B[Streamlit Interface]
    B --> C[FastAPI Backend]

    C --> D[Question Processing]
    D --> E[Embedding Model]
    E --> F[Chroma Vector Database]

    F --> G[Relevant Documentation]
    G --> H[LLM Provider]

    H --> I[Answer with Citations]
    I --> B

    C --> J[AI Agent]
    J --> K[RAG Search Tool]
    J --> L[LED Resistor Calculator]

    K --> F
    J --> H

RAG Architecture
mermaid
flowchart LR
    A[Arduino Documentation] --> B[Data Ingestion]
    B --> C[Data Cleaning]
    C --> D[Document Chunking]
    D --> E[Embedding Generation]
    E --> F[Chroma Vector Store]

    G[User Question] --> H[Question Embedding]
    H --> I[Semantic Retrieval]
    F --> I

    I --> J[Context Assembly]
    J --> K[Language Model]
    K --> L[Answer with Citations]

Data Flow
Arduino documentation is downloaded.
The ingestion module extracts useful information.
Data is cleaned and structured.
Documents are divided into meaningful chunks.
Embeddings are generated.
Chunks are stored in ChromaDB.
User questions are converted into embeddings.
Relevant chunks are retrieved.
Retrieved context is provided to the LLM.
The final answer is returned with citations.
7. Technology Stack
Technology	Purpose
Python	Main programming language
FastAPI	REST API backend
Streamlit	Interactive frontend
Requests	Documentation downloading
Pandas	Data analysis
Pydantic	Data validation
ChromaDB	Vector database
TF-IDF	Keyword-based intelligent search
Cosine Similarity	Similarity calculation
Embeddings	Semantic search
Groq / Gemini	Language model provider
Pytest	Automated testing
Ruff	Python linting
Git	Version control
GitHub	Source code management
Docker	Application containerization
GitHub Actions	Continuous integration
8. Data Sources

ArduinoMate uses official Arduino documentation as its primary knowledge source.

Source 1: Arduino Language Reference

https://github.com/arduino/reference-en

Source 2: Arduino Digital Read Documentation

https://raw.githubusercontent.com/arduino/reference-en/master/Language/Functions/Digital%20IO/digitalRead.adoc

Data Collection and Processing

The documentation is downloaded into:

data/raw/

The ingestion module processes the downloaded documents and extracts:

Function name.
Category.
Syntax.
Return information.
Common gotcha.
Source URL.

The cleaned data is stored in:

data/records.json

Source URLs are preserved to support traceability and citations.

9. Project Folder Structure
text
sanjivani-sj-61-arduinomate/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── records.py
│   ├── cli.py
│   ├── ingest.py
│   ├── fetch.py
│   ├── llm.py
│   ├── chunking.py
│   ├── embed.py
│   ├── vectorstore.py
│   ├── smart_search.py
│   ├── rag.py
│   ├── tools.py
│   ├── agent_loop.py
│   └── graph.py
│
├── data/
│   ├── raw/
│   ├── records.json
│   └── sample_records.py
│
├── prompts/
│   ├── system.txt
│   ├── question_answering.txt
│   └── summarization.txt
│
├── eval/
│   ├── eval_set.json
│   ├── run_eval.py
│   ├── search_results.md
│   └── prompt_compare.md
│
├── analysis/
│   └── explore.py
│
├── ui/
│   └── app.py
│
├── tests/
│   ├── test_records.py
│   ├── test_search.py
│   ├── test_api.py
│   ├── test_rag.py
│   └── test_tools.py
│
├── docs/
│   ├── how_llms_work.md
│   ├── interview.md
│   ├── resume.md
│   └── screenshots/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── PROGRESS.md

10. Installation and Setup
Prerequisites

Install the following:

Python 3.11 or newer.
Git.
VS Code or another Python editor.
Internet connection.
API key for the selected LLM provider.
Step 1: Clone the Repository
bash
git clone https://github.com/YOUR_GITHUB_USERNAME/sanjivani-sj-61-arduinomate.git

bash
cd sanjivani-sj-61-arduinomate

Step 2: Create Virtual Environment
bash
python -m venv .venv


Activate the environment.

Windows:

bash
.venv\Scripts\activate


Linux / macOS:

bash
source .venv/bin/activate

Step 3: Install Dependencies
bash
pip install -r requirements.txt

Step 4: Configure Environment Variables

Create a .env file in the project root.

env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key


Never upload your actual API keys to GitHub.

Step 5: Run FastAPI
bash
uvicorn app.main:app --reload


The API runs at:

http://127.0.0.1:8000

Step 6: Open API Documentation

Visit:

http://127.0.0.1:8000/docs

FastAPI provides interactive Swagger API documentation.

Step 7: Run Streamlit
bash
streamlit run ui/app.py

11. API Documentation

ArduinoMate exposes REST API endpoints through FastAPI.

Method	Endpoint	Purpose
GET	/health	Check API health
GET	/records	Retrieve Arduino records
GET	/records/{id}	Retrieve one record
GET	/search?q=	Search Arduino records
POST	/questions	Submit an Arduino question
POST	/chat	Ask the LLM assistant
GET	/search/semantic?q=	Perform semantic search
POST	/ask	Get a RAG-based answer
POST	/agent	Interact with the AI agent
Health Check
http
GET /health


Example response:

json
{
  "status": "healthy"
}

Search Records
http
GET /search?q=digitalRead

Ask ArduinoMate
http
POST /ask
Content-Type: application/json


Example request:

json
{
  "question": "What is digitalRead in Arduino?",
  "board": "Arduino Uno"
}


Example response structure:

json
{
  "answer": "digitalRead() reads the state of a specified digital pin.",
  "citations": [
    {
      "source": "Arduino Digital I/O Reference",
      "url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/"
    }
  ]
}


Actual API response fields depend on the implemented backend.

12. AI and RAG Implementation
Why RAG?

General-purpose language models may generate inaccurate Arduino information, especially when questions involve specific board capabilities or technical details.

RAG improves answer relevance by retrieving documentation before generating an answer.

RAG Components

1. Document Fetching

Downloads Arduino documentation using Python Requests with timeouts and error handling.

2. Document Cleaning

Extracts relevant information while removing unnecessary formatting.

3. Document Chunking

Splits documents into manageable sections while preserving code blocks, titles, and board-specific notes.

4. Embedding Generation

Converts documentation chunks into numerical vector representations.

5. Vector Database

Stores document embeddings and metadata in ChromaDB.

6. Semantic Search

Retrieves relevant documentation based on the meaning of a question.

7. Answer Generation

Uses retrieved context to generate an answer with source citations.

Important Design Consideration

Arduino documentation includes AsciiDoc files, code blocks, and board-specific tables.

ArduinoMate aims to preserve complete code sketches and attach board-specific information to relevant chunks.

This is important because Arduino Uno, Nano, and ESP32 do not necessarily have identical hardware capabilities.

13. AI Agent Implementation

ArduinoMate includes an AI agent capable of selecting and executing tools.

Available Tools
Tool	Purpose
RAG Search	Searches Arduino documentation
LED Resistor Calculator	Calculates an appropriate E12 resistor
Board Context	Supports board-specific information retrieval
Agent Workflow
mermaid
flowchart TD
    A[User Question] --> B[AI Agent]
    B --> C{Select Appropriate Tool}

    C -->|Documentation Question| D[RAG Search]
    C -->|LED Calculation| E[Resistor Calculator]

    D --> F[Collect Tool Result]
    E --> F

    F --> G[Generate Final Answer]
    G --> H[Return Answer to User]


The agent should use approval controls for actions requiring confirmation and should not invent results when tools fail.

14. Data Analysis and Evaluation

ArduinoMate includes an evaluation process to measure data quality, retrieval performance, and answer reliability.

Data Analysis

The analysis/explore.py module uses Pandas to explore collected Arduino records.

It reports:

Total number of Arduino function records.
Most common function category.
Distribution of records by category.
Search Evaluation

The project evaluates:

Keyword search.
TF-IDF search.
Semantic search.
Different chunk sizes.
Different retrieval top-k values.
Evaluation Dataset

The evaluation dataset contains Arduino questions, including questions that cannot be answered from the available knowledge base.

An important test is the unknown-question test.

If a question cannot be answered using retrieved documentation, ArduinoMate should respond:

"I don't know based on the available Arduino documentation."

This helps reduce unsupported answers.

Evaluation Metrics
Metric	Purpose
Retrieval Accuracy	Measures relevance of retrieved records
Precision@K	Measures relevant results among the top K
Recall@K	Measures retrieval coverage
Response Quality	Evaluates answer usefulness
Citation Accuracy	Checks whether citations support answers
Latency	Measures response time
Token Usage	Measures LLM token consumption
Evaluation Results

Update this table with actual measurements after running the evaluation.

Configuration	Chunk Size	Top K	Result
Configuration A	To be measured	3	Pending
Configuration B	To be measured	5	Pending
15. Testing

ArduinoMate uses Pytest for automated testing.

Testing includes:

Record loading.
Record searching.
Category counting.
API health checks.
Missing record handling.
RAG question answering using a fake LLM.
LED resistor calculations.
AI agent tool execution.

Run tests:

bash
pytest -v


Run Ruff:

bash
ruff check .


All required tests and lint checks should pass before merging code into the main branch.

16. Docker Setup

ArduinoMate can be containerized using Docker.

Build and start the application:

bash
docker compose up --build


Stop the containers:

bash
docker compose down


The Docker configuration should start the FastAPI backend and Streamlit interface with the required dependencies and environment variables.

17. Continuous Integration

GitHub Actions automates code quality and testing.

The CI workflow performs:

Python dependency installation.
Ruff linting.
Pytest execution.
Docker image building.

Workflow location:

.github/workflows/ci.yml

Feature branches should be merged only after the required CI checks pass.

18. Security and Production Considerations

ArduinoMate includes the following production improvements:

API key management through environment variables.
.env excluded from Git.
Request input validation.
Input length limits.
Error handling.
Request latency logging.
Token usage tracking.
Response caching.
Prompt-injection testing.
Documentation source validation.
Controlled tool execution.
Prompt Injection Protection

Retrieved documents and user inputs must be treated as untrusted content.

The assistant should follow its system instructions and must not execute arbitrary instructions found inside retrieved documentation.

19. Screenshots and Demo

Add actual screenshots of the running application in this section.

ArduinoMate User Interface

!ArduinoMate UI

Arduino Uno Pin Map

!Arduino Uno Pin Map

FastAPI Swagger Documentation

!FastAPI Swagger

RAG Answer with Citations

!RAG Answer

Demo Video

Add the actual demonstration video link here:

YOUR_DEMO_VIDEO_URL

20. Development Roadmap
Phase	Development Work
Day 01	Python introduction, variables, f-strings and menu
Week 1	Arduino records and documentation ingestion
Week 2	FastAPI backend and data analysis
Week 3	LLM integration and prompt engineering
Week 4	Chunking, embeddings and vector database
Week 5	RAG implementation and evaluation
Week 6	AI agent and tools
Week 7	Streamlit UI and Arduino pin map
Week 8	Testing and Docker
Week 9	CI/CD and deployment
Week 10	Production improvements
Final	Documentation and demo preparation
21. Future Enhancements

Possible future improvements include:

Support for additional Arduino-compatible boards.
Interactive circuit diagrams.
Arduino code explanation.
Arduino sketch debugging assistant.
Circuit simulation integration.
Additional electronics calculators.
Voice-based Arduino assistance.
Multilingual explanations.
Personalized learning paths.
Advanced board-specific documentation retrieval.
22. Conclusion

ArduinoMate aims to simplify Arduino programming and electronics learning through artificial intelligence.

By combining official Arduino documentation, Retrieval-Augmented Generation, semantic search, and AI agents, the system provides a structured approach to answering technical questions.

Its documentation knowledge base, LED resistor calculator, board-specific information, and interactive pin visualization make it a useful learning platform for students and electronics enthusiasts.

The project demonstrates how Python, FastAPI, Streamlit, vector databases, and modern language models can be integrated to develop a practical AI-powered educational application.

<p align="center">
**ArduinoMate – Learn Arduino Smarter. Build Projects Better. 🚀**
</p>
