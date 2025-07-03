# suno-automation Project

This project is an automation tool for generating songs from Suno.com ang reviewing them. It consists of a Python backend and a React frontend built with Vite.

### Tech Stack

**Frontend:**
* **Framework:** Vite
* **Language:** TypeScript
* **UI Libraries:**
    * React
    * Tailwind CSS
* **State Management:** Built-in React hooks
* **Linter:** Eslint
* **Formatter:** Prettier

**Backend:**
* **Language:** Python
* **Key Libraries:** 
    * (To be determined based on `requirements.txt`)
* **Data Storage:** Local filesystem
* **Linter:** Ruff
* **Formatter:** Black

### Project Structure

```
suno-automation/
├── backend/
│   ├── camoufox_user_data/
│   ├── configs/
│   ├── data/
│   ├── downloaded_songs/
│   ├── lab/
│   ├── lib/
│   ├── logs/
│   ├── misc/
│   ├── utils/
│   ├── main.py
│   ├── README.md
│   ├── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   ├── routes/
│   ├── constants/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── README.md
└── context.md
```

### Key Functionality
- Backend handles data processing and automation tasks
- Frontend provides UI for managing and viewing generated songs
- Uses local file storage for persistence
