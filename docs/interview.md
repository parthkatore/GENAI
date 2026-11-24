# ArduinoMate Interview Prep

## 60-second pitch

ArduinoMate is an AI learning assistant for people who are new to Arduino. Beginners can find official documentation difficult to navigate, while a general-purpose chatbot can invent APIs or give board-specific advice that is wrong. ArduinoMate uses a FastAPI backend and a Streamlit interface. It chunks Arduino reference pages and structured function records, embeds them with Gemini, stores vectors in ChromaDB, and uses retrieval-augmented generation to ground answers from a Groq-hosted language model. Responses include citations, and the system is designed to refuse questions its documentation cannot answer. It also has semantic search, an agent with a documentation-search tool, and an LED resistor calculator. I added tests, request limits, caching, logging, Docker, and CI. The most important lesson was that retrieval quality depends on preserving the source's meaning: Arduino facts often vary by board, so tables and code examples must stay connected to the right board. I am careful to distinguish the project's evaluated results from its current deployment readiness.

## Ten likely interview questions

### 1. What problem does ArduinoMate solve?

It helps Arduino beginners get answers grounded in reference material rather than relying on an unconstrained chatbot. Arduino APIs and hardware details can vary by board, so the app returns citations and is intended to say when its indexed documentation does not support an answer.

### 2. Why did you use RAG instead of sending every question directly to an LLM?

RAG retrieves a small set of relevant Arduino passages and supplies them as context to the model. That makes answers easier to trace to their sources and gives the application a basis for refusing unsupported questions. It also avoids sending the entire reference collection with every request.

### 3. What is the request flow?

The Streamlit frontend sends a question to FastAPI. The backend embeds the query with the Gemini embedding API, searches the persistent ChromaDB collection, and passes retrieved text to the configured chat model. The response includes the answer, citations, retrieval count, and an out-of-scope flag.

### 4. Why use Gemini and Groq?

They have separate roles in this version: Gemini creates compatible document and query embeddings, while Groq provides the chat completion. The vector index is built using the Gemini key even when Groq is selected as the chat provider. Without that key, the index stays empty and RAG cannot answer.

### 5. How did you evaluate retrieval and answer quality?

I used a 15-question evaluation set and compared chunking/retrieval configurations, plus a separate set of manual semantic-search queries. The repository records the earlier winning configuration and its measurements. Those numbers describe that evaluation run; they are not a guarantee that the current deployment is available or that every board-specific case is covered.

### 6. What was the hardest engineering challenge?

The hardest challenge is board-specific correctness. `analogRead()` resolution, allowed PWM pins, and operating voltage differ across boards. The official AsciiDoc pages encode important differences in tables and example sketches, so treating each page as generic prose can lose the very context that makes an answer correct. My current chunker still strips AsciiDoc tables and does not guarantee that long code examples remain intact. I would address this by preserving code blocks as atomic chunks, retaining board-table rows, tagging chunks with board metadata, and adding regression tests that compare Uno and Nano ESP32 answers. I do not claim that board-aware chunking is finished in the current code.

### 7. How do you handle unsupported questions?

The retriever filters results by a similarity threshold, and the prompt tells the model to answer only from retrieved context. If there are no relevant results in a ready index, the API returns the project's out-of-scope response. If the index itself is empty or unavailable, the API now returns HTTP 503 instead, because an indexing failure is not evidence that a question is out of scope.

### 8. What can the agent do?

The agent can search the Arduino documentation or call an LED resistor calculator. The calculator applies Ohm's law, `R = (Vs - Vf) / I`, and rounds up to an E12 resistor value. There is a hand-written ReAct loop and a LangGraph version with conversation memory and an approval step.

### 9. What production safeguards did you add?

The API has request-size and input-length limits, prompt-injection checks, latency and token logging, and a short-lived in-memory response cache. The project is containerized and has CI checks for linting, tests, and Docker builds. The test suite mocks model and vector-store calls so it does not require credentials.

### 10. What would you improve next?

First, I would complete board-aware parsing and re-run retrieval evaluation after rebuilding the index. I would also add explicit readiness checks and operational alerts for the embedding dependency. At the time of this prep, the local environment has no Gemini embedding key and the public Render API is suspended, so I would restore those before claiming a live end-to-end demo.

## Demo-day reminder

Before presenting, verify `/health` reports `rag_status: "ready"` and a nonzero `indexed_chunks` count. The current local RAG setup needs `GEMINI_API_KEY` in `.env`, and the deployed API must be resumed before a live demo can be rehearsed.
