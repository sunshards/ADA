# ADA - Automatic Dungeon Adventure


https://github.com/user-attachments/assets/87c569f5-adb3-4d51-8329-92c01f10920f


> **"Every now and then, a product comes along that changes everything.."**

Role-playing is fantastic... but it requires time, organization, and a group. Often, we have none of these. The result? Those who want to play can't, and those who don't deserve to play... do anyway.

**We want to change this with ADA.**

ADA is a multiplayer text adventure powered by state-of-the-art AI for quick, spontaneous, and immersive sessions. No preparation required.

## Key Features

### 1. Instant Character Generation
Gone are the days of tedious manual entry. ADA streamlines the onboarding process:
* **Natural Language Input:** Simply answer a few prompt questions or describe your hero in plain English.
* **Stat-Block Ready:** The system instantly compiles your description into a fully playable character sheet, complete with stats and attributes.

<img width="450" alt="Screenshot From 2026-02-04 15-57-02" src="https://github.com/user-attachments/assets/9bedb135-6491-4eee-9205-12b101c21316" />

### 2. The Dynamic AI Game Master
ADA acts as an omnipresent storyteller, managing the flow of the game in real-time:
* **World Building:** Automatically generates settings and weaves complex plots tailored to the group.
* **Adaptive Narratives:** The story isn't static; ADA responds dynamically to player choices, shifting the plot as the party explores.

<img width="450" alt="Screenshot From 2026-02-04 15-57-36" src="https://github.com/user-attachments/assets/b745af55-dc2a-4f14-b8ba-09020b37800d" />

### 3. Hybrid Logic System (Hallucination-Free)
The core innovation of ADA is the separation of "Flavor" and "Rules." It reacts to natural language but relies on a rigid backend for mechanics, ensuring the AI **never hallucinates game rules.**

<img width="450" alt="Screenshot From 2026-02-04 16-02-42" src="https://github.com/user-attachments/assets/d66f4bf9-1efd-4ec7-9181-7e406bc410b9" />

* **Database Grounding:**
    * The AI cannot invent non-existent weaponry or spells.
    * All Items, Skills, Enemies, and Locations are strictly pulled from the definitions in the MongoDB/JSON database.
* **Logic-Based Combat:**
    * While you narrate your attack in text, the system calculates the outcome using strict math.
    * Damage rolls, hit rates, and item consumption are handled by code, not the LLM.
 

### 4. Game Integrity & Balance
ADA ensures the game remains fair and consistent for all players:
* **The Morality Gatekeeper:** Validates that actions align with a character's established alignment and backstory, preventing "out-of-character" exploits.
* **Anti-Abuse System:** A built-in referee that prevents "god-moding" by cross-referencing every action against the ruleset before execution.

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
