# Educational Content Analysis System

A full-stack AI-powered educational content analysis system with semantic search and conversational assistant capabilities. Built with Django backend, React frontend, PostgreSQL, Qdrant vector database, and OpenAI integration.

## 🚀 Quick Start

```bash
# 1. Set OpenAI API key
export OPENAI_API_KEY='your-api-key-here'

# 2. Start all services
docker compose up -d

# 3. Access the application
# Frontend: http://localhost
# API: http://localhost/backend/api
# API Docs: http://localhost/backend/api/docs
```

## 🏗️ Architecture

### Technology Stack
- **Frontend**: React with Material-UI
- **Backend**: Django with Django Ninja REST API
- **Databases**: PostgreSQL (main) + Qdrant (vector search)
- **Queue**: Redis + RQ for background processing
- **AI**: OpenAI GPT-4o models + embeddings
- **Infrastructure**: Docker Compose with Nginx reverse proxy

### Service Architecture
```
Browser → Nginx (80) → Frontend (3000) → Backend API (8000)
                     ↘ Direct API calls (/backend/*)
                     
Backend → Redis Queue → Worker → OpenAI API
       ↘ PostgreSQL
       ↘ Qdrant Vector DB
```

### Container Services
- **nginx**: Reverse proxy with CORS handling
- **frontend**: React application
- **backend**: Django API server
- **worker**: Background job processor
- **db**: PostgreSQL database
- **redis**: Queue and cache
- **qdrant**: Vector database for embeddings

## ✨ Features

### Educational Content Analysis
- **AI-Powered Analysis**:
  - Key concept extraction (max 5 concepts)
  - Difficulty level assessment (beginner/intermediate/advanced/expert)
  - Study time estimation based on content complexity
- **Hybrid Search**: Combines PostgreSQL full-text search with Qdrant vector similarity
- **Asynchronous Processing**: Background analysis using Redis Queue
- **CRUD Operations**: Full content management with soft deletion

### Conversational Assistant
- **Context-Aware Chat**: Maintains conversation history and context
- **RAG Integration**: Retrieves relevant educational content to answer questions
- **Session Management**: Persistent conversation sessions per user
- **Token Tracking**: Monitors API usage and costs

### Debug Toolbar
- **Real-time Monitoring**: View API calls, embeddings, and search results
- **Development Aid**: Helps debug RAG pipeline and content retrieval
- **Toggle Visibility**: Can be hidden/shown as needed

## 🔧 Configuration

### Model Configuration
The system uses different OpenAI models optimized for specific tasks:

```python
# Analysis Models
ANALYSIS_KEY_CONCEPTS_MODEL = "gpt-4o-mini"      # Fast extraction
ANALYSIS_DIFFICULTY_MODEL = "gpt-4o-mini"         # Quick assessment
ANALYSIS_STUDY_TIME_MODEL = "gpt-4o"              # Complex reasoning

# Search Models  
SEARCH_KEYWORD_EXTRACTION_MODEL = "gpt-3.5-turbo" # Keyword extraction

# Conversation Models
CONVERSATION_ASSISTANT_MODEL = "gpt-4o"           # Advanced dialogue

# Embedding Models
EMBEDDING_MODEL_TYPE = "openai"                   # or "sentence-transformers"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
```

### Environment Variables
Create a `.env` file in the backend directory:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional (with defaults)
DB_NAME=content_management
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
DEBUG=True
SECRET_KEY=your-secret-key
```

## 📡 API Endpoints

### Content Analysis
```
POST   /api/content                    # Submit content for analysis
GET    /api/content                    # List all content
GET    /api/content/{id}               # Get specific content  
DELETE /api/content/{id}               # Soft delete content
GET    /api/content/{id}/status        # Check analysis status
POST   /api/content/{id}/reanalyze     # Trigger re-analysis
```

### User Management
```
POST   /api/users                      # Create user
GET    /api/users/{id}                 # Get user details
```

### Conversational Assistant
```
POST   /api/users/{id}/sessions        # Create conversation session
GET    /api/users/{id}/sessions        # List user's sessions
GET    /api/sessions/{id}/messages     # Get session messages
POST   /api/sessions/{id}/messages     # Send message to assistant
DELETE /api/sessions/{id}              # Delete session
```

### System
```
GET    /api/health                     # Health check
GET    /api/jobs/stats                 # Background job statistics
GET    /api/docs                       # Auto-generated API documentation
```

## 📝 Usage Examples

### 1. Content Analysis Workflow

```bash
# Create a user
curl -X POST http://localhost/backend/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@example.com"
  }'
# Response: {"id": 1, "username": "student1", ...}

# Submit content for analysis
curl -X POST http://localhost/backend/api/content \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Introduction to Machine Learning",
    "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed...",
    "user_id": 1
  }'
# Response: {"id": 1, "name": "Introduction to Machine Learning", "processed": false, ...}

# Check analysis status
curl http://localhost/backend/api/content/1/status
# Response: {"status": "processing"} or {"status": "completed"}

# Get analyzed content
curl http://localhost/backend/api/content/1
# Response includes key_concepts, difficulty_level, estimated_study_time
```

### 2. Conversational Assistant Usage

```bash
# Create a conversation session
curl -X POST http://localhost/backend/api/users/1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learning about ML"
  }'
# Response: {"id": "550e8400-e29b-41d4-a716-446655440000", "title": "Learning about ML", ...}

# Send a message
curl -X POST http://localhost/backend/api/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Can you explain the key concepts from my machine learning content?"
  }'
# Response: {"role": "assistant", "content": "Based on your content...", "relevant_contents": [...]}

# Get conversation history
curl http://localhost/backend/api/sessions/550e8400-e29b-41d4-a716-446655440000/messages
# Response: Array of messages with context
```

### 3. Search and RAG

The conversational assistant automatically:
1. Analyzes your question
2. Extracts keywords using GPT-3.5-turbo
3. Performs hybrid search (keyword + vector similarity)
4. Retrieves relevant content chunks
5. Generates contextual responses using GPT-4o

Example conversation flow:
```json
// User message
{
  "content": "What are the main algorithms in machine learning?"
}

// System performs behind the scenes:
// - Keyword extraction: ["algorithms", "machine learning"]
// - Vector search with embeddings
// - Retrieves relevant content chunks
// - Generates response with context

// Assistant response
{
  "role": "assistant",
  "content": "Based on your educational materials, the main machine learning algorithms include:\n\n1. **Supervised Learning**:\n   - Linear Regression\n   - Decision Trees\n   - Support Vector Machines...",
  "relevant_contents": [
    {
      "content_id": 1,
      "chunk": "Machine learning algorithms can be categorized into...",
      "similarity_score": 0.89
    }
  ]
}
```

### 4. Test Credentials

For testing, you can use:
```bash
# Create test user
username: testuser123
password: password123
email: testuser@example.com

# Create test content
name: "Test Content"
content: "Any educational material you want to analyze..."
```

## 💻 Development

### Local Development Setup

```bash
# Backend development
cd backend
uv sync                      # Install dependencies
python manage.py migrate     # Run migrations
python manage.py runserver   # Start API server
python run_worker.py         # Start worker (separate terminal)

# Frontend development  
cd frontend
npm install                  # Install dependencies
npm start                    # Start dev server

# Start required services
docker compose up -d redis db qdrant
```

### Docker Commands

```bash
# Rebuild and restart all services
docker compose down && docker compose up --build -d

# View logs
docker compose logs -f
docker compose logs -f backend worker

# Access container shell
docker compose exec backend bash
docker compose exec frontend sh

# Scale workers
docker compose up -d --scale worker=3

# Clean up
docker compose down -v        # Remove volumes
docker system prune -a       # Clean unused resources
```

### Docker Testing

Test your Docker setup with the included utility script:

```bash
# Test complete Docker environment
./test-docker-setup.sh       # Validates all services and connections

# The script checks:
# - Docker and Docker Compose installation
# - Service health and connectivity  
# - API endpoints and responses
# - Container logs and status
```

### Testing

```bash
# Run all tests with coverage
cd backend
python run_tests.py all

# Test options
python run_tests.py unit      # Unit tests only
python run_tests.py integration # Integration tests only
python run_tests.py fast      # Without coverage
python run_tests.py watch     # Watch mode
python run_tests.py coverage  # Generate HTML report

# Run in Docker
docker compose run --rm backend uv run pytest
```

### Frontend/E2E Testing

The frontend includes Cypress for end-to-end testing:

```bash
# Frontend unit tests
cd frontend
npm test                     # Run React unit tests

# Cypress E2E tests
npm run cy:open             # Open Cypress UI for interactive testing
npm run cy:run              # Run all Cypress tests headlessly

# Individual test suites
npm run cy:app-navigation   # Test app navigation
npm run cy:content-management # Test content management
npm run cy:chat-functionality # Test chat features
npm run cy:full-workflow    # Test complete user workflow

# Full-stack E2E testing
npm run e2e                 # Start frontend and run E2E tests
npm run e2e:open           # Start frontend and open Cypress UI
```

**Cypress Test Structure:**
```
frontend/cypress/
├── e2e/                    # End-to-end test files
│   ├── app-navigation.cy.js
│   ├── content-management.cy.js
│   ├── chat-functionality.cy.js
│   └── full-user-workflow.cy.js
├── support/                # Support files and commands
│   ├── e2e.js
│   └── commands.js
└── cypress.config.js       # Cypress configuration
```

### Test Structure
```
backend/tests/
├── conftest.py              # Fixtures and configuration
├── factories.py             # Test data factories
├── unit/                    # Unit tests
│   ├── test_models.py      
│   ├── test_services.py    
│   └── test_llms.py        
└── integration/             # API integration tests
    ├── test_api_content.py  
    └── test_api_chat.py     
```

## 🔒 Security

- **Authentication**: User isolation - users only see their own content
- **Input Validation**: Comprehensive sanitization for all inputs
- **CORS Protection**: Configured for specific origins
- **Environment Security**: API keys stored in environment variables
- **Soft Deletion**: Content is marked as deleted, not permanently removed

## ⚡ Performance Optimizations

### Database Optimizations
- **Custom Managers**: `ActiveManager` filters soft-deleted items automatically
- **Query Optimization**: N+1 query elimination with `select_related` and `prefetch_related`
- **Strategic Indexes**: Covering indexes for common query patterns
- **Efficient Pagination**: Bounded limits (1-100) with validation

### Vector Search
- **Hybrid Search**: Combines keyword and semantic search with weighted scoring
- **Embedding Cache**: Reuses embeddings to reduce API calls
- **Similarity Threshold**: Configurable relevance cutoff

### Service Layer
- **ContentService**: Handles validation and sanitization
- **SessionService**: Manages conversation sessions
- **MessageService**: Processes chat messages
- **UserService**: User validation and management

## 📚 Cursor Development Rules

### Rebuild Commands
```bash
# Quick rebuild
rebuild: docker compose down && docker compose up --build -d
```

### Python Import Standards
- Always place all imports at the top of the file
- No imports inside functions or methods
- Use absolute imports for internal code:
  ```python
  # Good
  from app.services import ContentService
  
  # Bad
  from services import ContentService
  ```
- Group imports in order:
  1. Standard library imports
  2. Third-party imports  
  3. Local application imports
- Separate each group with a blank line

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   sudo lsof -i :80 :3000 :8000
   
   # Kill process using port
   sudo kill -9 <PID>
   ```

2. **Database Connection Issues**
   ```