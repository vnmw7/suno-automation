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
  - `ruff` and `black` for linting/formatting
  - `uvicorn` for ASGI server

### Frontend
- **Framework**: RemixJS (TypeScript)
- **UI Libraries**: 
  - React 18
  - Tailwind CSS for styling
- **State Management**: React Context API
- **Authentication**: Supabase Auth

## Project Structure
```
suno-automation/
├── backend/               # FastAPI backend
│   ├── api/               # API routes
│   ├── configs/           # Configuration files
│   ├── utils/             # Utility functions
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

## Testing
### Backend Testing
Run tests with pytest:
```bash
cd backend
pytest
```

### Frontend Testing
Run tests with Jest:
```bash
cd frontend
npm test
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