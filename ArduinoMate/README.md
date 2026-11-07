# ArduinoMate – Week 1 Development

Welcome to **ArduinoMate**, an intelligent, beginner-friendly backend platform designed to index, explore, analyze, and smartly search Arduino microcontroller documentation, sensor libraries, and project records.

This project implements:
1. **FastAPI Web Service**: High-performance REST API with five documented endpoints.
2. **Pandas Data Exploration**: Dynamic statistical facts computed directly from real records.
3. **Machine Learning Smart Search**: Natural Language Processing using **TF-IDF Vectorization** and **Cosine Similarity** ranking.
4. **Automated Testing Suite**: 25 automated unit and integration tests.

---

## 📁 Project Structure

```text
ArduinoMate/
│
├── app/
│   ├── __init__.py           # Application package marker
│   ├── main.py               # FastAPI application and endpoint definitions
│   └── smart_search.py       # TF-IDF & Cosine Similarity search engine
│
├── analysis/
│   ├── __init__.py           # Analysis package marker
│   └── explore.py            # Pandas data exploration and statistical analysis
│
├── data/
│   ├── records.json          # Primary dataset of 16 Arduino reference records
│   └── questions.json        # Persistent storage for user-submitted questions
│
├── tests/
│   ├── __init__.py           # Test suite package marker
│   ├── run_tests.py          # Unified test runner
│   ├── test_api.py           # Automated tests for all 5 FastAPI endpoints
│   ├── test_explore.py       # Automated tests for Pandas data analysis
│   └── test_smart_search.py  # Automated tests for TF-IDF ranking & caching
│
├── README.md                 # Project documentation and usage guide
└── requirements.txt          # Production and testing Python dependencies
```

---

## ⚙️ Requirements

- **Python**: Version `3.10` or newer (Python `3.11`, `3.12`, or `3.13` recommended)
- **Pip**: Latest Python package manager

### Core Libraries
- `fastapi>=0.110.0`: Modern, high-performance web framework.
- `uvicorn>=0.28.0`: Lightning-fast ASGI web server.
- `pydantic>=2.0.0`: Robust data validation and JSON serialization.
- `pandas>=2.2.0`: Data analysis and tabular manipulation library.
- `scikit-learn>=1.4.0`: Machine learning algorithms (TF-IDF & Cosine Similarity).
- `numpy>=1.26.0`: Numerical computing utilities.
- `httpx>=0.27.0`: HTTP client for API interaction.
- `pytest>=8.0.0`: Testing framework.

---

## 🚀 Installation & Setup

### 1. Navigate to the Project Root
```bash
cd ArduinoMate
```

### 2. Create and Activate a Virtual Environment (Recommended)
On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the FastAPI Server

Start the development server with live reload enabled:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, the server output will display:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
[ArduinoMate] Application started. Loaded 16 records.
```

---

## 📖 Interactive Swagger API Documentation

FastAPI automatically generates interactive API documentation. While the server is running, open your web browser and visit:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

From Swagger UI, you can click on any endpoint, press **"Try it out"**, fill in parameters, and click **"Execute"** to see live responses.

---

## 📊 Running the Pandas Data Analysis

To inspect the dataset and print dynamic statistical facts:

```bash
python analysis/explore.py
```

### Example Terminal Output:
```text
=================================================================
         ARDUINOMATE DATA EXPLORATION REPORT (Pandas)        
=================================================================

[Fact 1] Total Number of Records:
         -> 16 verified Arduino records in dataset.

[Fact 2] Most Common Category:
         -> 'LED projects' with 2 records (12.5% of total).
         Category breakdown:
           * LED projects           : 2 record(s)
           * Temperature sensors    : 2 record(s)
           * LCD displays           : 2 record(s)
           * Servo motors           : 2 record(s)
           * Arduino programming    : 2 record(s)
           * Robotics               : 2 record(s)
           * Bluetooth projects     : 2 record(s)
           * Ultrasonic sensors     : 1 record(s)
           * Automation             : 1 record(s)

[Fact 3] Keyword Presence Across Titles & Descriptions:
           * 'sensor    ' :  7 record(s) (43.8%) #######
           * 'led       ' :  5 record(s) (31.2%) #####
           * 'motor     ' :  4 record(s) (25.0%) ####
           * 'i2c       ' :  2 record(s) (12.5%) ##
           * 'display   ' :  2 record(s) (12.5%) ##
           * 'bluetooth ' :  2 record(s) (12.5%) ##
           * 'robotics  ' :  0 record(s) ( 0.0%) 

[Fact 4] Tag Statistics:
         -> Total unique tags: 82
         Top 5 most frequent tags:
           * #sensor             : 5 time(s)
           * #robotics           : 3 time(s)
           * #motor              : 3 time(s)
           * #bluetooth          : 2 time(s)
           * #temperature        : 2 time(s)

[Data Quality Check]:
         -> Clean dataset! No missing/null values detected.
=================================================================
```

---

## 🌐 API Endpoint Documentation

### 1. `GET /health`
Verifies API status and dataset loading health.

- **Example Request**:
  ```http
  GET /health HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Example Response (HTTP 200)**:
  ```json
  {
    "status": "healthy",
    "service": "ArduinoMate API",
    "version": "1.0.0",
    "total_records": 16,
    "timestamp": "2026-11-07T08:21:43.792709+00:00"
  }
  ```

---

### 2. `GET /records?limit=`
Retrieves records with an optional `limit` query parameter.

- **Example Request (Limit = 2)**:
  ```http
  GET /records?limit=2 HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Example Response (HTTP 200)**:
  ```json
  [
    {
      "id": 1,
      "title": "Blinking LED with Pushbutton Switch",
      "description": "Learn basic digital input and output with Arduino. Read a momentary tactile pushbutton on a digital input pin and toggle an LED on digital pin 13 with software debouncing.",
      "category": "LED projects",
      "tags": ["LED", "digitalRead", "digitalWrite", "pushbutton", "GPIO", "beginner"]
    },
    {
      "id": 2,
      "title": "RGB LED Color Fader Using PWM",
      "description": "Create smooth color transitions with an RGB LED using Pulse Width Modulation (PWM). Control red, green, and blue brightness levels independently using analogWrite pins.",
      "category": "LED projects",
      "tags": ["LED", "RGB", "PWM", "analogWrite", "color", "analog"]
    }
  ]
  ```
- **Error Handling (Invalid Limit <= 0)**:
  ```json
  {
    "detail": "Limit must be a positive integer greater than 0."
  }
  ```

---

### 3. `GET /records/{id}`
Retrieves a specific Arduino record by its unique integer identifier.

- **Example Request**:
  ```http
  GET /records/5 HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Example Response (HTTP 200)**:
  ```json
  {
    "id": 5,
    "title": "HC-SR04 Ultrasonic Distance Meter and Parking Sensor",
    "description": "Calculate distance to obstacles by emitting 40kHz ultrasound pulses and timing echo reflection with pulseIn. Trigger warning beeps and visual indicators as objects approach.",
    "category": "Ultrasonic sensors",
    "tags": ["ultrasonic", "distance", "HC-SR04", "pulseIn", "obstacle", "sensor"]
  }
  ```
- **Error Handling (ID Not Found, HTTP 404)**:
  ```json
  {
    "detail": "Record with ID 999 not found."
  }
  ```

---

### 4. `GET /search?q=`
Intelligent semantic search using Machine Learning (TF-IDF + Cosine Similarity).

- **Example Request**:
  ```http
  GET /search?q=ultrasonic%20sensor&limit=2 HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Example Response (HTTP 200)**:
  ```json
  {
    "query": "ultrasonic sensor",
    "total_matches": 2,
    "results": [
      {
        "id": 5,
        "title": "HC-SR04 Ultrasonic Distance Meter and Parking Sensor",
        "description": "Calculate distance to obstacles by emitting 40kHz ultrasound pulses and timing echo reflection with pulseIn. Trigger warning beeps and visual indicators as objects approach.",
        "category": "Ultrasonic sensors",
        "tags": ["ultrasonic", "distance", "HC-SR04", "pulseIn", "obstacle", "sensor"],
        "similarity_score": 0.5126
      },
      {
        "id": 14,
        "title": "Two-Wheel Drive (2WD) Obstacle Avoiding Autonomous Robot",
        "description": "Build an autonomous wheeled robot using an L298N H-bridge dual motor driver and an HC-SR04 ultrasonic sensor mounted on a scanning servo to navigate around obstacles.",
        "category": "Robotics",
        "tags": ["robotics", "L298N", "motor-driver", "obstacle-avoidance", "autonomous", "wheels"],
        "similarity_score": 0.1784
      }
    ]
  }
  ```
- **Empty Query Handling (HTTP 200)**:
  ```json
  {
    "query": "",
    "total_matches": 0,
    "results": [],
    "message": "Search query is empty. Please provide a search term."
  }
  ```

---

### 5. `POST /questions`
Submits a user question with automatic Pydantic schema validation.

- **Example Request**:
  ```http
  POST /questions HTTP/1.1
  Host: 127.0.0.1:8000
  Content-Type: application/json

  {
    "user_name": "Maya",
    "question": "How do I connect an I2C LCD to an Arduino Uno?",
    "category": "LCD displays"
  }
  ```
- **Example Response (HTTP 201 Created)**:
  ```json
  {
    "message": "Question submitted successfully.",
    "question_id": 1,
    "data": {
      "id": 1,
      "user_name": "Maya",
      "question": "How do I connect an I2C LCD to an Arduino Uno?",
      "category": "LCD displays",
      "created_at": "2026-11-07T08:21:43.850000+00:00"
    }
  }
  ```
- **Validation Failure Example (HTTP 422 Unprocessable Entity)**:
  If `question` has fewer than 5 characters or `user_name` is missing, Pydantic automatically rejects the payload with a structured validation error.

---

## 🧠 How TF-IDF and Cosine Similarity Work

Traditional keyword search simply checks whether an exact word appears in a string. It cannot determine **which** records are more important or relevant. Machine Learning smart search uses two foundational concepts:

### 1. TF-IDF (Term Frequency - Inverse Document Frequency)
TF-IDF converts text documents into numbers that a machine can understand:

- **Term Frequency (TF)**: How frequently a word appears in a specific document.
  $$\text{TF}(t, d) = \frac{\text{Count of word } t \text{ in document } d}{\text{Total words in document } d}$$
- **Inverse Document Frequency (IDF)**: How rare or unique a word is across the entire dataset.
  $$\text{IDF}(t) = \log\left(\frac{1 + \text{Total Documents}}{1 + \text{Documents containing word } t}\right) + 1$$
- **TF-IDF Score**:
  $$\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$$

**Why this matters**:
Common words like *"the"*, *"with"*, and *"on"* appear in almost every document, so their IDF score is near zero. Meanwhile, specialized words like *"ultrasonic"*, *"servo"*, or *"DHT11"* appear in only one or two documents, earning a high weight.

### 2. Cosine Similarity
Once each document and the user query are converted into numerical TF-IDF vectors, we compare their directions in multi-dimensional space.

$$\text{Cosine Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$

- **1.0 (Angle = 0°)**: Perfect match; the query and document share the exact same key topics.
- **0.5**: Strong thematic overlap.
- **0.0 (Angle = 90°)**: Completely unrelated; no shared terminology.

### 3. Smart Caching
Calculating the TF-IDF matrix takes CPU time. In `app/smart_search.py`, we calculate an MD5 hash of the dataset. As long as the dataset records remain unchanged, we **reuse the pre-computed TF-IDF matrix** and only vectorize the incoming query. This drops search latency to under **1 millisecond**.

---

## 🧪 Automated Testing

ArduinoMate includes 25 comprehensive unit and integration tests covering:
- All 5 API endpoints (success status, error handling, parameter limits, 404s, 422 validation).
- TF-IDF vectorization, cosine similarity ranking, empty queries, and matrix caching.
- Pandas dataset loading, dynamic fact calculation, and missing value resilience.

### Run All Tests with the Unified Runner:
```bash
python tests/run_tests.py
```

### Alternatively, Run with pytest:
```bash
pytest tests/ -v
```

---

## 🏷️ Week-1 Git Submission Commands

To commit all Week-1 deliverables and apply the exact `week-1` tag:

```bash
# 1. Stage all project files
git add ArduinoMate/

# 2. Commit with the required message
git commit -m "Complete ArduinoMate Week-1 implementation"

# 3. Create the exact week-1 tag
git tag week-1

# 4. Verify the tag was created
git tag -l
git show week-1
```

