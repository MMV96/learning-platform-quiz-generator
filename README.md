# Learning Platform Quiz Generator

Microservice per la generazione di quiz da contenuti testuali utilizzando l'intelligenza artificiale.

## 🎯 Panoramica

- **Linguaggio**: Python con FastAPI
- **Responsabilità**: Generare quiz da content tramite AI e salvare in MongoDB
- **Pattern**: Collection Ownership (OWNER della collection quizzes)
- **AI Provider**: Anthropic Claude
- **Database**: MongoDB condiviso (porta 27017)

## 📁 Struttura Progetto

```
learning-platform-quiz-generator/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── quiz.py               # Pydantic models per quiz
│   │   └── requests.py           # Request/Response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_client.py          # Anthropic integration
│   │   ├── database.py           # MongoDB connection
│   │   └── quiz_generator.py     # Core business logic
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging configuration
│       └── exceptions.py         # Custom exceptions
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Setup e Installazione

### 1. Clona il repository
```bash
git clone <repository-url>
cd learning-platform-quiz-generator
```

### 2. Crea environment virtuale
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. Installa dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configura environment
```bash
cp .env.example .env
# Modifica .env con le tue configurazioni
```

### 5. Avvia il servizio
```bash
# Sviluppo
uvicorn src.main:app --host 0.0.0.0 --port 80 --reload

# Produzione
python -m src.main
```

## 🐳 Docker

### Build dell'immagine
```bash
docker build -t quiz-generator .
```

### Esecuzione del container
```bash
docker run -p 80:80 --env-file .env quiz-generator
```

## 🔌 API Endpoints

### POST /generate-quiz
Genera un nuovo quiz da contenuto testuale.

**Request Body:**
```json
{
  "content": "Testo da cui generare il quiz (minimo 100 caratteri)",
  "book_id": "book_123",
  "metadata": {},
  "options": {
    "num_questions": 10,
    "difficulty_distribution": {
      "easy": 0.3,
      "medium": 0.5,
      "hard": 0.2
    },
    "question_types": ["multiple_choice", "boolean"],
    "language": "it"
  }
}
```

**Response:**
```json
{
  "quiz_id": "quiz_id_generated",
  "questions_count": 10,
  "status": "success",
  "generation_time_seconds": 5.23,
  "ai_model_used": "claude-3-sonnet-20240229"
}
```

### GET /quizzes/{quiz_id}
Recupera un quiz specifico.

### GET /quizzes
Lista quiz con filtri opzionali.

**Query Parameters:**
- `book_id`: Filtra per book ID
- `limit`: Numero di risultati (default: 10, max: 100)
- `offset`: Offset per paginazione (default: 0)

### DELETE /quizzes/{quiz_id}
Elimina un quiz.

### GET /health
Health check del servizio.

## 🗄️ Database Schema

**Collection**: `quizzes` in database `learning_platform`

```javascript
{
  _id: ObjectId,
  book_id: "string",
  questions: [{
    question: "string",
    type: "multiple_choice|boolean|open", 
    correct_answer: "string",
    options: ["string"], // optional for multiple_choice
    explanation: "string",
    difficulty: "easy|medium|hard",
    topic: "string",
    concepts_tested: ["string"]
  }],
  created_at: ISODate,
  ai_model: "string",
  generation_prompt: "string", // optional
  metadata: {} // optional
}
```

## ⚙️ Configurazione

Le configurazioni sono gestite tramite variabili d'ambiente:

```bash
# Service Configuration
SERVICE_NAME=quiz-generator
ENVIRONMENT=development

# Database
MONGODB_URL=mongodb://admin:password123@localhost:27017/learning_platform?authSource=admin

# AI API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here

# AI Configuration
DEFAULT_AI_MODEL=claude-3-sonnet-20240229
```

## 🧪 Test

```bash
# Esegui test (se disponibili)
pytest

# Test manual con curl
curl -X POST "http://localhost/generate-quiz" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Il machine learning è una branca dell intelligenza artificiale...",
    "book_id": "book_123"
  }'
```

## 📝 Logging

Il servizio utilizza il logging strutturato con diversi livelli:
- `DEBUG`: Ambiente di sviluppo
- `INFO`: Ambiente di produzione
- Logs specifici per database, AI client e business logic

## 🚨 Gestione Errori

Il servizio gestisce diversi tipi di errori:
- `QuizGenerationError`: Errori nella generazione quiz
- `QuizNotFoundError`: Quiz non trovato
- `DatabaseConnectionError`: Errori di connessione database
- `AIServiceError`: Errori del servizio AI

## 🔧 Sviluppo

### Aggiungere nuove feature
1. Modifica i modelli in `src/models/`
2. Implementa la logica in `src/services/`
3. Aggiungi endpoint in `src/main.py`
4. Aggiorna la documentazione

### Best Practices
- Segui il pattern Collection Ownership per MongoDB
- Usa logging strutturato
- Implementa proper error handling
- Mantieni la separazione delle responsabilità

## 📄 Licenza

[Inserire informazioni sulla licenza]