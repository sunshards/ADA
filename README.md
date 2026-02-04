# ADA - Automatic Dungeon Adventure


https://github.com/user-attachments/assets/87c569f5-adb3-4d51-8329-92c01f10920f


> **"Every now and then, a product comes along that changes everything.."**

Role-playing is fantastic... but it requires time, organization, and a group. Often, we have none of these. The result? Those who want to play can't, and those who don't deserve to play... do anyway.

**We want to change this with ADA.**

ADA is a multiplayer text adventure powered by state-of-the-art AI for quick, spontaneous, and immersive sessions. No preparation required.

## Key Features

<img width="1277" height="1325" alt="Screenshot From 2026-02-04 15-57-02" src="https://github.com/user-attachments/assets/9bedb135-6491-4eee-9205-12b101c21316" />
* **Automated Character Creation:** Just answer a few questions or provide a description, and ADA generates a complete, stat-block-ready character sheet instantly.

  <img width="1274" height="1472" alt="Screenshot From 2026-02-04 15-57-36" src="https://github.com/user-attachments/assets/b745af55-dc2a-4f14-b8ba-09020b37800d" />

* **The AI Game Master:** ADA finds the group, creates the setting, and weaves the plot in real-time, adapting dynamically to player choices.


<img width="1274" height="1472" alt="Screenshot From 2026-02-04 16-02-42" src="https://github.com/user-attachments/assets/d66f4bf9-1efd-4ec7-9181-7e406bc410b9" />
* **Hybrid Logic System:** ADA reacts to your natural language descriptions but **does not hallucinate game mechanics**.
    * **Database Grounding:** Items, skills, enemies, and locations are strictly pulled from the MongoDB database. The AI cannot invent items that do not exist in the JSON/DB definitions.
    * **Logic-Based Combat:** The system interprets your text actions but applies strict game rules for damage, hit rates, and item usage.
* **Alignment & Morality Engine:** The system acts as a "Gatekeeper," validating that player actions align with their character's morality and righteousness.
* **Anti-Abuse System:** Keeps the game balanced by validating actions against the ruleset, preventing "god-moding."

## 🛠️ Tech Stack

* **Backend:** Python (Flask, Socket.IO)
* **AI:** OpenRouter (LLM integration)
* **Database:** MongoDB (Atlas/Cloud)
* **Frontend:** HTML/JS (Real-time interactions)

---

## Getting Started

### Prerequisites

1.  **Python** (Managed via `uv` recommended).
2.  **OpenRouter Account:** Get an API key from [openrouter.ai](https://openrouter.ai).
3.  **MongoDB Atlas:** Create a cluster at [mongodb.com](https://www.mongodb.com).

### 1. Database Setup

You must create a MongoDB database and populate it with the game data.

1.  Create a database on MongoDB Atlas (e.g., `ADADatabase`).
2.  Follow the structure of the provided JSON examples. You need to create the following collections:
    * `Users`
    * `Characters`
    * `Items`
    * `Skills`
    * `Enemies`
    * `Classes`

### 2. Environment Configuration

Create a `.env` file inside the `src/` folder.

```bash
# /src/.env

# Your OpenRouter API Key
OPENROUTER_API_KEY=sk-or-your-actual-key-here

# Your MongoDB Connection String
# Replace <username> and <password> with your actual credentials.
CONNECTION_STRING="mongodb+srv://<username>:<password>@cluster.mongodb.net/"
```

### 3. AI Model Configuration
Open src/brain.py. You can configure the list of free or paid models to use. The system automatically handles fallback if a model is unavailable.

```python
# src/brain.py

# Updated list of free models (Check OpenRouter for latest)
FREE_MODELS = [
    "arcee-ai/trinity-large-preview:free",
    "google/gemini-2.0-flash-exp:free",
    # Add other models here
]
```

### Running the Project
Ensure you have uv installed. Run the entry point from the root directory:
```bash
uv run python main.py
```

Open your browser and navigate to http://127.0.0.1:5004 (or the port specified in the console).

## The Team
* **[Stefano Emanuele Aldanese](https://github.com/StefanoAldanese)** - Programmer & Game Logic
* **[Donato D'Ambrosio](https://github.com/Donny1301)** - Programmer & Database Implementation
* **[Simone Boscaglia](https://github.com/sunshards)** - Programmer & UI Designer
