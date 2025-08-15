# Smart Todo List with AI

A full-stack web application with AI integration for intelligent task management. This system uses daily context (messages, emails, notes) to provide intelligent task management suggestions including prioritization, deadline recommendations, and context-aware task enhancement.

##  Features

### Backend (Django REST Framework)
- **Task Management**: Complete CRUD operations for tasks
- **AI-Powered Analysis**: Task prioritization, deadline suggestions, and context-aware recommendations
- **Context Processing**: Daily context entries from WhatsApp, emails, and notes
- **Smart Categorization**: Auto-suggest task categories and tags
- **Task Enhancement**: Improve task descriptions with context-aware details
- **Statistics & Analytics**: Task completion rates, priority distributions

### Frontend (Next.js)
- **Dashboard**: Task overview with AI-powered insights
- **Task Management Interface**: Create/edit tasks with AI suggestions
- **Context Input Page**: Daily context management
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Real-time Updates**: Live task statistics and notifications

### AI Integration
- **Priority Scoring**: Uses AI to rank tasks based on urgency and context (0-1 scale)
- **Deadline Optimization**: Recommends realistic deadlines based on task complexity
- **Context Analysis**: Processes daily context for sentiment and priority indicators
- **Smart Suggestions**: Auto-categorization and tag recommendations
- **Multi-AI Support**: OpenAI, Anthropic Claude, Google Gemini, and LM Studio

## Screenshots

### Dashboard
<img width="1917" height="946" alt="smart" src="https://github.com/user-attachments/assets/b98299bc-dd1c-44e3-842f-c85f5c9ad8de" />

*Main dashboard showing task statistics and recent tasks with AI priority scores*

## 🛠️ Tech Stack

### Backend
- **Framework**: Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **AI Integration**: OpenAI API, Anthropic Claude API, Google Gemini API, LM Studio
- **Language**: Python 3.8+

### Frontend
- **Framework**: Next.js 15 with App Router
- **Styling**: Custom CSS (Tailwind CSS compatible)
- **Language**: JavaScript/JSX
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Notifications**: React Hot Toast

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- PostgreSQL (optional - SQLite works for development)
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart_todo_project/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create `.env` file in the backend directory:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   DB_NAME=smart_todo_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   GEMINI_API_KEY=your_gemini_key_here
   LM_STUDIO_URL=http://localhost:1234/v1
   ```

5. **Setup database**
   ```bash
   # For PostgreSQL (optional)
   createdb smart_todo_db
   
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create default categories**
   ```bash
   python manage.py shell
   ```
   ```python
   from tasks.models import Category
   
   categories = [
       {'name': 'Work', 'color': '#3B82F6'},
       {'name': 'Personal', 'color': '#10B981'},
       {'name': 'Health', 'color': '#F59E0B'},
       {'name': 'Education', 'color': '#8B5CF6'},
       {'name': 'Shopping', 'color': '#EF4444'},
       {'name': 'Communication', 'color': '#06B6D4'},
       {'name': 'Development', 'color': '#84CC16'},
       {'name': 'Meetings', 'color': '#F97316'},
   ]
   
   for cat_data in categories:
       Category.objects.get_or_create(
           name=cat_data['name'],
           defaults={'color': cat_data['color']}
       )
   
   print("Default categories created!")
   exit()
   ```

7. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start the backend server**
   ```bash
   python manage.py runserver
   ```
   Backend will be available at `http://127.0.0.1:8000/`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
   ```

4. **Start the frontend server**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000/`

## 📚 API Documentation

### Base URL
```
http://127.0.0.1:8000/api/
```

### Authentication
Currently uses Django's default session authentication. For production, implement JWT or Token authentication.

### Endpoints

#### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/` | List all tasks with filtering options |
| POST | `/tasks/` | Create new task with AI enhancement |
| GET | `/tasks/{id}/` | Retrieve specific task |
| PUT | `/tasks/{id}/` | Update task |
| DELETE | `/tasks/{id}/` | Delete task |
| POST | `/tasks/ai_analysis/` | Get AI analysis without creating task |
| POST | `/tasks/{id}/reanalyze/` | Re-run AI analysis on existing task |
| GET | `/tasks/statistics/` | Get task statistics |

#### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories/` | List all categories |
| POST | `/categories/` | Create new category |
| PUT | `/categories/{id}/` | Update category |
| DELETE | `/categories/{id}/` | Delete category |

#### Context Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contexts/` | List context entries with filtering |
| POST | `/contexts/` | Create context entry |
| POST | `/contexts/bulk_create/` | Create multiple context entries |
| GET | `/contexts/insights_summary/` | Get context insights summary |

### Sample API Requests

#### Create Task with AI Enhancement
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare quarterly presentation",
    "description": "Create slides for Q3 review meeting",
    "use_ai_enhancement": true
  }'
```

#### Get AI Analysis
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ai_analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_title": "Review project documentation",
    "task_description": "Go through all technical docs",
    "current_workload": 7
  }'
```

#### Add Context Entry
```bash
curl -X POST http://127.0.0.1:8000/api/contexts/ \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Meeting with client tomorrow at 2 PM regarding project requirements",
    "source_type": "EMAIL",
    "sender": "client@example.com",
    "timestamp": "2025-08-15T10:00:00Z"
  }'
```

## 🤖 Sample Tasks and AI Suggestions

### Sample Task 1: Work Meeting
**Input:**
```json
{
  "title": "Team standup meeting",
  "description": "Weekly team sync"
}
```

**AI Analysis:**
```json
{
  "ai_priority_score": 0.6,
  "suggested_category": "Meetings",
  "suggested_tags": ["meeting", "work", "weekly"],
  "ai_suggested_deadline": "2025-08-16T09:00:00Z",
  "enhanced_description": "Weekly team standup meeting to discuss project progress, blockers, and upcoming priorities."
}
```

### Sample Task 2: Urgent Development
**Input:**
```json
{
  "title": "Fix critical bug in production",
  "description": "Payment gateway is down"
}
```

**AI Analysis:**
```json
{
  "ai_priority_score": 0.95,
  "suggested_category": "Development",
  "suggested_tags": ["urgent", "bug", "production"],
  "ai_suggested_deadline": "2025-08-15T18:00:00Z",
  "enhanced_description": "Critical production issue: Payment gateway is experiencing downtime. Immediate investigation and fix required to restore service."
}
```

### Sample Context Processing
**Input:**
```json
{
  "content": "Can you please review the quarterly report by Friday? It's quite urgent!",
  "source_type": "EMAIL",
  "sender": "manager@company.com"
}
```

**AI Processing Results:**
```json
{
  "keywords": ["review", "quarterly", "report", "friday", "urgent"],
  "sentiment_score": 0.3,
  "priority_indicators": ["urgent", "friday"],
  "urgency_level": 8
}
```

## 🔧 Configuration Options

### AI Service Configuration
The application supports multiple AI providers:

1. **LM Studio (Recommended for local development)**
   - Download from https://lmstudio.ai/
   - Install a model (Llama 2, Mistral, etc.)
   - Start local server on http://localhost:1234

2. **OpenAI API**
   - Set `OPENAI_API_KEY` in environment variables
   - Uses GPT-3.5-turbo for analysis

3. **Anthropic Claude**
   - Set `ANTHROPIC_API_KEY` in environment variables
   - Uses Claude-3 for enhanced reasoning

4. **Google Gemini**
   - Set `GEMINI_API_KEY` in environment variables
   - Uses Gemini Pro for multimodal analysis

### Fallback Behavior
If AI services are unavailable, the system uses intelligent fallback logic:
- Priority scoring based on keyword analysis
- Category suggestions using pattern matching
- Deadline estimation based on task complexity indicators

