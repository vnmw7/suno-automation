# Suno Automation - Full-Stack Application

![Project Logo](https://via.placeholder.com/150) <!-- Add actual logo later -->

A full-stack application that automates song generation using Suno.ai API, featuring a FastAPI backend and RemixJS frontend.

## Features
- 🎵 Automated song generation via Suno.ai API
- 🚀 FastAPI backend for API management
- ⚛️ RemixJS frontend with React components
- 🔐 User authentication and session management
- 📊 Dashboard for tracking generated songs

## Tech Stack
### Backend
- **Framework**: FastAPI (Python)
- **Libraries**: 
  - `nodriver`, `selenium_driverless` for browser automation
  - `openai` for AI integration
  - `supabase` for database
  - `pandas` for data processing
- **Tools**: 
  - `ruff` for fast Python linting and code analysis
  - `black` for consistent code formatting
  - `uvicorn` for ASGI server
- **Testing**: pytest for backend unit and integration tests

### Frontend
- **Framework**: RemixJS (TypeScript)
- **UI Libraries**: 
  - React 18
  - Tailwind CSS for styling
- **State Management**: React Context API
- **Authentication**: Supabase Auth
- **Tools**:
  - `ESLint` with TypeScript and React configurations
  - `Prettier` for code formatting
  - `TypeScript` for type checking

## Project Structure
```
suno-automation/
├── backend/               # FastAPI backend
│   ├── api/               # API routes
│   ├── configs/           # Configuration files
│   ├── services/              # <--- NEW: For business logic and external services
│   │   ├── __init__.py
│   │   └── supabase_service.py # <--- ALL your Supabase logic goes here
│   ├── tests/             # Directory for all tests
│   │   ├── conftest.py    # Shared pytest fixtures for the backend
│   │   ├── test_api/
│   │   └── test_utils/
│   ├── utils/             # Utility functions
│   ├── uploads/
│   │   ├── pending_review/
│   │   └── approved/
│   └── main.py            # Entry point
├── frontend/              # RemixJS frontend
│   ├── app/               # Application code
│   │   ├── routes/        # Page routes
│   │   └── components/    # UI components
│   └── public/            # Static assets
└── README.md              # Project documentation
```

## Getting Started
### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL database

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/suno-automation.git
   cd suno-automation
   ```

2. Set up backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. Set up frontend:
   ```bash
   cd ../frontend
   npm install
   ```

4. Create `.env` files:
   - Backend: `backend/.env`
     ```
     DATABASE_URL=postgresql://user:password@localhost:5432/suno
     SUNO_API_KEY=your_suno_api_key
     ```
   - Frontend: `frontend/.env`
     ```
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_ANON_KEY=your-anon-key
     ```

### Running the Application
1. Start backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at:
   - API Docs: `http://localhost:8000/docs`
   - Frontend: `http://localhost:3000`

## Code Quality & Linting

### Backend Linting (Python)
The backend uses **Ruff** for fast Python linting and **Black** for code formatting.

#### Setup Ruff Configuration
Create a `pyproject.toml` file in the `backend/` directory:
```toml
[tool.ruff]
# Exclude common directories
exclude = [
    ".git", ".venv", "__pycache__", "build", "dist", 
    "camoufox_session_data", "node_modules"
]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E4", "E7", "E9",  # pycodestyle errors
    "F",               # Pyflakes
    "W",               # pycodestyle warnings
    "B",               # flake8-bugbear
    "I",               # isort
    "N",               # pep8-naming
    "UP",              # pyupgrade
    "C4",              # flake8-comprehensions
    "PIE",             # flake8-pie
    "PT",              # flake8-pytest-style
    "RUF",             # Ruff-specific rules
]

ignore = [
    "T201",    # print statements (useful for debugging)
    "PLR0913", # too-many-arguments
    "PLR0912", # too-many-branches
]

[tool.ruff.lint.per-file-ignores]
"**/test_*.py" = ["PLR2004", "S101"]  # Allow magic values and assertions in tests
"lab/**/*.py" = ["T201", "F401"]     # Relaxed rules for lab files

[tool.black]
line-length = 88
target-version = ['py310']
```

#### Linting Commands
```bash
cd backend

# Check for linting issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code with Black
black .

# Check formatting without changing files
black . --check

# Run both linting and formatting
ruff check . --fix && black .
```

### Frontend Linting (TypeScript/React)
The frontend uses **ESLint** with TypeScript and React configurations.

#### ESLint Configuration
The project includes comprehensive ESLint rules in `.eslintrc.cjs`:
- TypeScript strict rules
- React best practices
- Accessibility (a11y) checks
- Import organization
- Code quality standards

#### Linting Commands
```bash
cd frontend

# Check for linting issues
npm run lint

# Auto-fix issues
npm run lint:fix

# Strict linting (fails on warnings)
npm run lint:check

# Format code with Prettier
npm run format

# Check formatting
npm run format:check

# Type checking
npm run typecheck
```

#### Pre-commit Workflow
For the best development experience, run these commands before committing:

**Backend:**
```bash
cd backend
ruff check . --fix
black .
pytest  # Run tests
```

**Frontend:**
```bash
cd frontend
npm run lint:fix
npm run format
npm run typecheck
npm test  # Run tests when available
```

## Testing

### Backend Testing with Pytest
The backend uses **pytest** for comprehensive Python testing with fixtures, mocking, and coverage reporting.

#### Setup Pytest Configuration
Add testing dependencies to `requirements.txt`:
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
httpx>=0.24.0  # For testing FastAPI endpoints
```

Create `pytest.ini` in the `backend/` directory:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-exclude=*/tests/*
    --cov-exclude=*/venv/*
    --cov-exclude=*/camoufox_session_data/*
asyncio_mode = auto
```

#### Test Structure
```
backend/tests/
├── conftest.py              # Shared pytest fixtures
├── test_main.py            # Test main.py endpoints
├── test_api/
│   ├── __init__.py
│   ├── test_auth/
│   │   └── test_routes.py
│   └── test_song/
│       └── test_routes.py
├── test_utils/
│   ├── __init__.py
│   ├── test_ai_functions.py
│   └── test_suno_functions.py
└── test_lib/
    ├── __init__.py
    ├── test_login.py
    └── test_supabase.py
```

#### Sample Test Files

**conftest.py** - Shared fixtures:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    return MagicMock()

@pytest.fixture
def sample_song_request():
    """Sample song request data"""
    return {
        "strBookName": "Genesis",
        "intBookChapter": 1,
        "strVerseRange": "1-5",
        "strStyle": "Pop",
        "strTitle": "Test Song"
    }
```

**test_main.py** - API endpoint tests:
```python
import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client):
    """Test root endpoint returns expected message"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "server working"}

def test_generate_verse_ranges(client):
    """Test verse ranges generation endpoint"""
    response = client.post(
        "/generate-verse-ranges?book_name=Genesis&book_chapter=1"
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "verse_ranges" in data

@pytest.mark.asyncio
async def test_song_structure_generation(client, sample_song_request):
    """Test song structure generation"""
    response = client.post("/generate-song-structure", json=sample_song_request)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

#### Testing Commands
```bash
cd backend

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run tests matching pattern
pytest -k "test_song"

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x

# Run tests in parallel (install pytest-xdist first)
pytest -n auto
```

### Frontend Testing with Jest
The frontend uses **Jest** with React Testing Library for component and integration testing.

#### Setup Jest Configuration
Add testing dependencies to `package.json`:
```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.1.4",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^14.5.1",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@types/jest": "^29.5.8",
    "ts-jest": "^29.1.1"
  }
}
```

Create `jest.config.js` in the `frontend/` directory:
```javascript
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapping: {
    '^~/(.*)$': '<rootDir>/app/$1',
  },
  testMatch: [
    '**/__tests__/**/*.(ts|tsx|js)',
    '**/*.(test|spec).(ts|tsx|js)'
  ],
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    '!app/**/*.d.ts',
    '!app/entry.client.tsx',
    '!app/entry.server.tsx',
    '!app/root.tsx'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  }
};
```

#### Test Structure
```
frontend/tests/
├── setup.ts                # Jest setup file
├── __mocks__/              # Mock files
│   └── supabase.ts
├── components/
│   ├── Header.test.tsx
│   └── SongForm.test.tsx
├── routes/
│   ├── _index.test.tsx
│   └── dashboard.test.tsx
└── utils/
    └── auth.test.ts
```

#### Sample Test Files

**tests/setup.ts** - Jest setup:
```typescript
import '@testing-library/jest-dom';

// Mock Remix modules
jest.mock('@remix-run/react', () => ({
  ...jest.requireActual('@remix-run/react'),
  useLoaderData: jest.fn(),
  useActionData: jest.fn(),
  useNavigation: jest.fn(() => ({ state: 'idle' })),
}));
```

**Component test example**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SongForm } from '~/components/SongForm';

describe('SongForm', () => {
  test('renders form fields correctly', () => {
    render(<SongForm />);
    
    expect(screen.getByLabelText(/book name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/chapter/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/verse range/i)).toBeInTheDocument();
  });

  test('submits form with correct data', async () => {
    const mockSubmit = jest.fn();
    render(<SongForm onSubmit={mockSubmit} />);
    
    await userEvent.type(screen.getByLabelText(/book name/i), 'Genesis');
    await userEvent.type(screen.getByLabelText(/chapter/i), '1');
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(mockSubmit).toHaveBeenCalledWith({
      bookName: 'Genesis',
      chapter: 1
    });
  });
});
```

#### Testing Commands
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test SongForm.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="form"

# Update snapshots
npm test -- --updateSnapshot
```

#### Package.json Scripts
Add these scripts to `frontend/package.json`:
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --coverage --watchAll=false"
  }
}
```

### Testing Best Practices

#### Backend (Pytest)
- Use fixtures for common test data and mocked dependencies
- Test both success and error scenarios
- Mock external services (Supabase, OpenAI, browser automation)
- Use `pytest-asyncio` for testing async functions
- Aim for >80% code coverage

#### Frontend (Jest)
- Test user interactions, not implementation details
- Mock external dependencies and API calls
- Use React Testing Library queries (`getByRole`, `getByLabelText`)
- Test accessibility features
- Snapshot test for UI components that rarely change

#### Integration Testing
```bash
# Backend integration tests
cd backend
pytest tests/integration/ -v

# Frontend E2E tests (if using Playwright/Cypress)
cd frontend
npm run test:e2e
```

## Contributing
We welcome contributions! Please follow these steps:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes with descriptive messages
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
For support or questions, please open an issue in the GitHub repository.