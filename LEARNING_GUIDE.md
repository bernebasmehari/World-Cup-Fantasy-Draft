# WorldDraft — Complete Build Guide
### How we built a live fantasy draft app for the 2026 FIFA World Cup, step by step

---

## Who this is for

This guide assumes you know roughly what Python and JavaScript are, but have never
built a full-stack web app before. Every step explains not just *what* to type, but
*why* we made each decision.

---

## 0. What we're building

WorldDraft is a fantasy draft app where 5 friends each pick 5 national teams from
the 48-team 2026 World Cup. The teams earn points based on real tournament results:
wins, draws, goals scored, and how far the team advances. A live leaderboard shows
who's winning the fantasy competition.

The app has four parts:
1. A **database** (PostgreSQL) that stores teams, users, draft picks, and accounts
2. A **backend API** (Python / FastAPI) that reads and writes the database
3. A **frontend** (React / TypeScript) that users interact with in a browser
4. **Deployment** (Railway + Vercel) so it runs on the internet, not just your laptop

---

## 1. Project layout

```
WorldDraft/
├── backend/          ← Python API
│   ├── app/
│   │   ├── main.py         ← entry point, registers all routes
│   │   ├── database.py     ← connects to Postgres
│   │   ├── scoring.py      ← fantasy points logic
│   │   ├── models/         ← one file per database table
│   │   │   ├── team.py
│   │   │   ├── user.py
│   │   │   ├── draftteam.py
│   │   │   └── account.py
│   │   └── routes/         ← one file per group of API endpoints
│   │       ├── teamsroute.py
│   │       ├── usersroute.py
│   │       ├── authroute.py
│   │       └── syncroute.py
│   ├── requirements.txt    ← Python dependencies
│   └── Procfile            ← tells Railway how to start the server
└── frontend/         ← React app
    ├── src/
    │   ├── App.tsx          ← root component, holds login state
    │   └── pages/
    │       ├── Home.tsx     ← login/register + join room
    │       ├── Draft.tsx    ← live snake draft grid
    │       ├── Leaderboard.tsx
    │       └── Roster.tsx
    ├── .env.example         ← documents required env variables
    └── vercel.json          ← tells Vercel how to serve the React app
```

**Why this split?**
The backend and frontend are completely separate programs. The backend is an API
(just JSON over HTTP, no HTML). The frontend is a JavaScript app that runs entirely
in the user's browser and talks to the backend via `fetch()` calls. This separation
means you can deploy them independently, swap out either one, or let multiple
frontends share the same backend.

---

## 2. Setting up the database (PostgreSQL)

PostgreSQL is a relational database — it stores data in tables with rows and columns,
like Excel but much more powerful and designed for software.

### Why PostgreSQL?
- Free and open source
- Handles multiple users reading/writing at the same time (concurrent access)
- FastAPI + SQLAlchemy have excellent support for it
- Railway (our deployment platform) provides managed PostgreSQL for free

### Install PostgreSQL locally
Download from https://postgresql.org. During install, set a password. The default
port is `5432` and the default user is `postgres`.

After install, open pgAdmin (the GUI that ships with PostgreSQL) and create a new
database called `worlddraft`.

### The connection string
```
postgresql://postgres:YOUR_PASSWORD@localhost:5432/worlddraft
```
Breaking that down:
- `postgresql://` — the protocol (database type)
- `postgres` — the username
- `YOUR_PASSWORD` — the password you set during install
- `localhost` — the server (your own machine)
- `5432` — the port number PostgreSQL listens on
- `worlddraft` — the name of the specific database

---

## 3. Backend setup (FastAPI)

### Why FastAPI?
FastAPI is a Python framework for building web APIs. We chose it because:
- Very fast to write — you define an endpoint as a Python function
- Automatic documentation at `/docs` (Swagger UI) — visit it in your browser while developing
- Built-in request validation via Pydantic
- Async-capable for high concurrency

### Create a virtual environment
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows PowerShell
# or: source venv/bin/activate   # Mac/Linux
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv requests httpx
```

**Why a virtual environment?**
It isolates this project's dependencies from every other Python project on your
machine. Without it, installing a package globally can break other projects that
need a different version of the same package. Think of it as a sandbox — everything
you `pip install` while the venv is active stays inside that folder and doesn't
affect anything else.

### Pin your dependencies
After installing everything, run:
```bash
pip freeze > requirements.txt
```
This writes a file listing every package and its exact version. When Railway deploys
your code on their servers, they read this file and install the exact same versions,
guaranteeing the same behavior in production as on your laptop.

### `backend/app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/worlddraft"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**What is SQLAlchemy?**
SQLAlchemy is an ORM (Object-Relational Mapper). Instead of writing raw SQL like
`SELECT * FROM teams WHERE id = 5`, you write Python like `db.query(Team).get(5)`.
It translates your Python into SQL automatically.

- `create_engine` opens a connection pool to the database.
- `SessionLocal` is a factory — every time you call it you get a fresh "session"
  (a conversation with the database).
- `Base` is the base class all our models will inherit from.
- `get_db()` is a **dependency** — FastAPI will call this before each request and
  automatically close the DB session when the request is done. The `yield` keyword
  makes it a generator; code before `yield` runs before the request, code after runs
  after (like a try/finally).

**Why not hardcode the DB URL in production?**
The URL contains a password. You never commit passwords to git. In production,
`DATABASE_URL` is set as an environment variable on Railway and read with
`os.getenv("DATABASE_URL")`.

---

## 4. Database models (tables)

Each model is a Python class that maps to one table in PostgreSQL. SQLAlchemy
reads these classes and creates the actual SQL tables.

### `backend/app/models/team.py`
```python
from sqlalchemy import Column, Integer, String
from ..database import Base

class Team(Base):
    __tablename__ = "teams"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, unique=True, index=True)
    group          = Column(String, nullable=True)
    group_wins     = Column(Integer, default=0)
    group_draws    = Column(Integer, default=0)
    group_losses   = Column(Integer, default=0)
    goals_scored   = Column(Integer, default=0)
    furthest_round = Column(String, default="group_stage")
```

- `primary_key=True` — this column uniquely identifies each row and auto-increments
- `index=True` — creates a database index on that column for fast lookups (like a book index)
- `unique=True` — the database enforces no two rows can have the same value here
- `default=0` — if you insert a row without specifying that field, it's 0
- `nullable=True` — this column is allowed to be NULL (empty)

`furthest_round` stores a string like `"round_of_16"` instead of a number because
strings are self-documenting — you never have to remember "what does stage 3 mean?"

### `backend/app/models/user.py`
```python
class User(Base):
    __tablename__ = "user"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, index=True)
    room_code   = Column(String, index=True)
    draft_order = Column(Integer, nullable=True)
```

A User is someone who joins a draft room. Note: `name` is NOT `unique=True` because
the same person can join multiple rooms under the same username. The combination of
`(name, room_code)` is unique, which we enforce in the route logic rather than the
table definition.

`room_code` is a short string like `"WORLD26"` that friends share to join the same
draft. This means everyone in one game has the same `room_code`.

### `backend/app/models/draftteam.py`
```python
from sqlalchemy import Column, Integer, String, ForeignKey

class DraftTeam(Base):
    __tablename__ = "draft_teams"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("user.id"), index=True)
    team_id     = Column(Integer, ForeignKey("teams.id"), index=True)
    pick_number = Column(Integer, index=True)
    room_code   = Column(String, index=True)
```

This is a **junction table** (also called a join table or association table). It
connects users to teams. A junction table is the standard way to model a
many-to-many relationship: one user drafts many teams; one team could be drafted
in a different room by a different user.

`ForeignKey("user.id")` means `user_id` must reference a real row in the `user`
table. If you try to insert a `DraftTeam` pointing to a non-existent user, the
database rejects it. This is **referential integrity** — the database enforces
consistency automatically.

### `backend/app/models/account.py`
```python
class Account(Base):
    __tablename__ = "accounts"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
```

A separate table for login credentials, kept separate from the draft `User` table.
One `Account` (login) maps to potentially many `User` rows (one per room joined).

**Note on passwords:** Passwords here are stored plain-text. This is only acceptable
for a small private app where you know every user. In any public-facing app you must
hash passwords with a library like `bcrypt` or `argon2`. Hashing means the database
never stores the actual password — only a one-way fingerprint. Even if the database
is stolen, passwords can't be recovered.

---

## 5. Scoring system (`backend/app/scoring.py`)

```python
ROUND_ORDER = [
    "group_stage", "round_of_32", "round_of_16",
    "quarterfinal", "semifinal", "final", "champion"
]

KNOCKOUT_POINTS = {
    "group_stage": 0, "round_of_32": 2, "round_of_16": 4,
    "quarterfinal": 6, "semifinal": 8, "final": 10, "champion": 15
}

def group_stage_points(team):
    return team.group_wins * 3 + team.group_draws * 1

def goal_points(team):
    return team.goals_scored * 0.5

def knockout_points(team):
    return KNOCKOUT_POINTS.get(team.furthest_round, 0)

def team_points(team):
    return group_stage_points(team) + goal_points(team) + knockout_points(team)

def round_index(round_name):
    return ROUND_ORDER.index(round_name) if round_name in ROUND_ORDER else -1
```

**Design decisions:**

- **Knockout points are NOT stacked.** A team that reaches the semifinals earns
  exactly 8 points, not 2+4+6+8. This keeps the math clean and prevents
  double-counting. "What stage did they reach?" is a single fact stored as a string.

- **Goals are worth 0.5 each.** They're a tiebreaker and bonus, not the main
  scoring driver. This prevents a high-scoring group stage team from completely
  overwhelming the knockout stage advantage.

- **`round_index()` prevents going backwards.** When updating via the sync endpoint,
  we compare `round_index(current)` vs `round_index(new)` and only update if the
  new round is further along. This means running the sync 10 times won't corrupt data
  if FIFA's API temporarily returns incomplete information.

- **Pure functions, no database calls.** This file has zero database imports. It
  takes a `team` object and returns a number. This makes it trivially easy to test
  in isolation.

---

## 6. API routes

Routes are the "endpoints" — the URLs your frontend calls. FastAPI uses decorators
(`@router.get`, `@router.post`) to connect a URL pattern to a Python function.

### How to run the backend locally

```bash
cd backend
uvicorn app.main:app --reload
```

- `app.main` = the Python module path (file `backend/app/main.py`)
- `:app` = the FastAPI instance named `app` inside that file
- `--reload` = restart automatically when you save a file

Visit `http://localhost:8000/docs` for interactive Swagger documentation where you
can test every endpoint in your browser.

### `backend/app/routes/teamsroute.py` — key patterns

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.team import Team
from .. import scoring

router = APIRouter()

@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [{"id": t.id, "name": t.name, "points": scoring.team_points(t),
             "furthest_round": t.furthest_round} for t in teams]
```

`Depends(get_db)` is FastAPI's dependency injection. FastAPI sees
`db: Session = Depends(get_db)` and knows to call `get_db()` before the function
runs, pass the result in as `db`, and close it after. You never call `get_db()` yourself.

```python
@router.post("/teams/{team_id}/group-result")
def update_group_result(team_id: int, body: GroupResultBody, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    if body.result == "win":
        team.group_wins += 1
    elif body.result == "draw":
        team.group_draws += 1
    else:
        team.group_losses += 1
    team.goals_scored += body.goals
    db.commit()
    db.refresh(team)
    return {"id": team.id, "name": team.name, "points": scoring.team_points(team)}
```

- `{team_id}` in the URL is a **path parameter** — FastAPI extracts it automatically
- `body: GroupResultBody` is a Pydantic model; FastAPI reads the JSON request body
  and validates it (correct types, required fields) before your function runs
- `db.commit()` saves the changes to the database
- `db.refresh(team)` re-reads the row from the database so we return current data
- `HTTPException` with a status code returns an error response; the browser gets
  the HTTP status code and the `detail` field in the JSON body

```python
@router.get("/leaderboard/{room_code}")
def get_leaderboard(room_code: str, db: Session = Depends(get_db)):
    users    = db.query(User).filter(User.room_code == room_code).all()
    teams    = db.query(Team).all()
    picks    = db.query(DraftTeam).filter(DraftTeam.room_code == room_code).all()
    team_map = {t.id: t for t in teams}
    result   = []
    for user in users:
        user_picks = [p for p in picks if p.user_id == user.id]
        user_teams = [
            {"team": team_map[p.team_id].name,
             "points": scoring.team_points(team_map[p.team_id])}
            for p in user_picks if p.team_id in team_map
        ]
        total = sum(t["points"] for t in user_teams)
        result.append({"user": user.name, "total_points": total, "teams": user_teams})
    result.sort(key=lambda x: x["total_points"], reverse=True)
    return result
```

This queries three tables and assembles the result in Python. The `team_map` dict
`{t.id: t for t in teams}` is a dictionary comprehension — it creates a dict keyed
by team ID so lookups are O(1) instead of scanning the list every time.

---

## 7. Auth routes (`backend/app/routes/authroute.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.account import Account

router = APIRouter()

class AuthBody(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(body: AuthBody, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken.")
    account = Account(username=body.username, password=body.password)
    db.add(account)
    db.commit()
    return {"id": account.id, "username": account.username}

@router.post("/login")
def login(body: AuthBody, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.username == body.username).first()
    if not account or account.password != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"id": account.id, "username": account.username}
```

**Why no JWT tokens or sessions?**
For a small private app with 5 friends, returning `{id, username}` on login and
storing it in the browser's `localStorage` is sufficient. There's no financial data
or PII at risk. If this were a public app you'd issue a **JWT (JSON Web Token)** —
a signed token with an expiry time — and verify it on every request.

HTTP status codes matter:
- `400 Bad Request` — the input was invalid (username already taken)
- `401 Unauthorized` — the credentials were wrong
- `404 Not Found` — the resource doesn't exist
- `200 OK` — success (the default when you return normally)

---

## 8. FIFA sync route (`backend/app/routes/syncroute.py`)

This was the most complex part of the project. We wanted live results from FIFA's
website automatically.

### The problem: JavaScript SPAs

FIFA's standings page at `fifa.com` is a **Single Page App (SPA)**. When you visit
it, your browser downloads a nearly blank HTML file. Then JavaScript runs, makes
API calls, and fills in the data. If you just download the HTML with Python's
`requests` library, you get nothing useful — the data hasn't loaded yet.

### The solution: Playwright

We installed **Playwright**, a browser automation tool that controls a real Chrome
browser programmatically. We told it to:
1. Open the FIFA standings page
2. Listen to all network requests the page's JavaScript made
3. Find the actual API call that returned the standings data

The real API endpoint we discovered:
```
https://api.fifa.com/api/v3/calendar/17/285023/289273/standing?language=en&count=200
```

- `17` = competition ID (Men's World Cup)
- `285023` = season ID (2026)
- `289273` = stage ID (group stage)

Knockout stage IDs we found the same way:
```python
KNOCKOUT_STAGES = {
    "round_of_32":  289287,
    "round_of_16":  289288,
    "quarterfinal": 289289,
    "semifinal":    289290,
    "final":        289292,
}
```

### The problem: team name mismatches

FIFA calls it "Korea Republic" but our database has "South Korea". FIFA uses
accented characters like "Côte d'Ivoire" but matching strings with accents is
unreliable.

**Solution: normalization + overrides**

```python
import unicodedata, re

def _norm(name: str) -> str:
    # 1. Decompose accented chars: é → e + combining accent
    nfkd = unicodedata.normalize("NFKD", name)
    # 2. Drop the combining accents (non-ASCII bytes)
    ascii_name = nfkd.encode("ascii", "ignore").decode()
    # 3. Lowercase and keep only letters/digits
    return re.sub(r"[^a-z0-9]", "", ascii_name.lower())

# _norm("Côte d'Ivoire") → "cotedivoire"
# _norm("Korea Republic") → "korearepublic"
```

Then a manual overrides dictionary:
```python
FIFA_NAME_OVERRIDES = {
    "usa":           "United States",
    "korearepublic": "South Korea",
    "iran":          "IR Iran",
    # ... etc
}
```

### Making sync idempotent

**Idempotent** means calling the endpoint 10 times gives the same result as calling
it once. We SET values instead of incrementing them:

```python
# WRONG — calling twice doubles the count:
team.group_wins += wins

# RIGHT — calling twice is the same as calling once:
team.group_wins = wins
```

For `furthest_round`, we only advance forward:
```python
from ..scoring import round_index
if round_index(new_round) > round_index(team.furthest_round):
    team.furthest_round = new_round
```

---

## 9. Main entry point (`backend/app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .database import Base, engine
from .models.team import Team       # must import so SQLAlchemy knows about the table
from .models.user import User
from .models.draftteam import DraftTeam
from .models.account import Account
from .routes import teamsroute, usersroute, authroute, syncroute

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # create tables if they don't exist
    yield  # app runs here; code after yield runs on shutdown

app = FastAPI(lifespan=lifespan)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authroute.router)
app.include_router(teamsroute.router)
app.include_router(usersroute.router)
app.include_router(syncroute.router)
```

### What is CORS?

Browsers have a security feature called the **Same-Origin Policy**: JavaScript on
`worlddraft.vercel.app` is blocked from calling `worlddraft.railway.app` by default,
because they're different origins (different domains). This would break our app
completely.

**CORS (Cross-Origin Resource Sharing)** is how a server says "I trust this other
origin." The `CORSMiddleware` adds HTTP response headers like
`Access-Control-Allow-Origin: https://worlddraft.vercel.app` that tell the browser
"this request is allowed."

Without CORS configured correctly, every API call from the frontend would silently
fail with a browser console error, and the app would show nothing.

### `Base.metadata.create_all(bind=engine)`

This reads all classes that inherit from `Base` (all our models) and creates the
corresponding tables in PostgreSQL if they don't already exist. Safe to run every
time the server starts — it doesn't modify or delete existing tables.

**Why must we import the model files?** Python only knows about classes that have
been imported. If you don't `from .models.team import Team`, SQLAlchemy never sees
the `Team` class and never creates the `teams` table. The imports at the top of
`main.py` are what "registers" all the models.

---

## 10. Frontend setup (React + Vite + TypeScript)

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install react-router-dom
npm run dev   # starts dev server at http://localhost:5173
```

**Why Vite?**
Vite is a development server and build tool. It's much faster than the old
Create React App because it uses native ES modules during development (no bundling
step — just serve the files and let the browser handle imports) and uses esbuild
(written in Go, very fast) for production builds.

**Why TypeScript?**
TypeScript adds static types to JavaScript. You define the shape of your data:
```typescript
interface Team { id: number; name: string; points: number }
```
The compiler tells you when you access a field that doesn't exist, pass the wrong
type to a function, or forget to handle `null`. It catches entire categories of
bugs before you run the code.

**Why React?**
React lets you build UIs as components — reusable pieces that each manage their
own state. When state changes, React automatically re-renders the affected parts
of the page without you manually updating the DOM. This makes complex interactive
UIs much easier to reason about.

### Routing (`frontend/src/App.tsx`)

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useState } from 'react'

export interface Account { id: number; username: string }
const STORAGE_KEY = 'worlddraft_user'

function App() {
  const [account, setAccount] = useState<Account | null>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  })

  function handleLogin(a: Account) {
    setAccount(a)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(a))
  }

  function handleLogout() {
    setAccount(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <BrowserRouter>
      <NavBar account={account} onLogout={handleLogout} />
      <Routes>
        <Route path="/"            element={<Home account={account} onLogin={handleLogin} />} />
        <Route path="/draft"       element={<Draft />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/roster"      element={<Roster account={account} />} />
      </Routes>
    </BrowserRouter>
  )
}
```

**Why is account state in `App.tsx`?**
Multiple pages need to know who's logged in: NavBar shows the username, Roster
filters by username, Home shows a different UI when logged in vs logged out.
"Lifting state up" to the common ancestor (`App`) is the fundamental React pattern.
If you kept login state inside `Home.tsx`, the NavBar and Roster couldn't read it.

**Why localStorage?**
We want the user to stay logged in if they close and reopen the browser tab.
`localStorage` persists across page refreshes and browser restarts (unlike
`sessionStorage` which clears when the tab closes). The `useState` initializer
function (the `() => { ... }` argument) runs only once on first render, reading
whatever was saved previously.

**Why React Router?**
In a traditional website, clicking a link causes the browser to make a new HTTP
request and the server returns a new HTML page. In a React SPA (Single Page App),
there's only one HTML page. React Router intercepts navigation and swaps out
components instead of doing full page reloads. This makes navigation instant.

---

## 11. Making API calls from the frontend

Every page needs to fetch data from the backend. The pattern is always the same:

```typescript
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Inside a component:
const [teams, setTeams] = useState<Team[]>([])

useEffect(() => {
  fetch(`${API}/teams`)
    .then(r => r.json())
    .then(data => setTeams(data))
}, [])  // empty array = run once when component mounts
```

**`fetch()`** is a built-in browser API for making HTTP requests. It returns a
Promise (asynchronous — doesn't block the page while waiting for the server).

**`useEffect()`** is a React hook that runs code after the component renders. The
second argument (the dependency array) controls when it re-runs: `[]` means only
on mount, `[roomCode]` means every time `roomCode` changes.

**`useState()`** stores a value that, when changed via its setter, causes React to
re-render the component with the new value.

---

## 12. The snake draft (`frontend/src/pages/Draft.tsx`)

A snake draft means:
- Round 1: Player 1 → 2 → 3 → 4 → 5 (left to right)
- Round 2: Player 5 → 4 → 3 → 2 → 1 (right to left, "snake" back)
- Round 3: Player 1 → 2 → 3 → 4 → 5 (left to right again)
- etc.

The key math:
```typescript
// Given pick number (1-based) and player count, who is currently picking?
function playerForPick(pickNum: number, n: number): number {
  const idx   = pickNum - 1           // convert to 0-based
  const round = Math.floor(idx / n)   // which round (0-based)
  const pos   = idx % n               // position within the round
  return round % 2 === 0 ? pos : n - 1 - pos
  //             even round → L→R      odd round → R→L
}

// Given a round and a display column, what pick number is that cell?
function pickNumForCell(round: number, col: number, n: number): number {
  return round % 2 === 0
    ? round * n + col + 1           // even: column 0 = first pick of round
    : round * n + (n - 1 - col) + 1 // odd:  column 0 = LAST pick of round
}
```

**Example trace with n=3 players:**
| Pick | round | pos | player |
|------|-------|-----|--------|
| 1    | 0 (even) | 0 | 0 |
| 2    | 0 (even) | 1 | 1 |
| 3    | 0 (even) | 2 | 2 |
| 4    | 1 (odd)  | 0 | n-1-0 = 2 |
| 5    | 1 (odd)  | 1 | n-1-1 = 1 |
| 6    | 1 (odd)  | 2 | n-1-2 = 0 |
| 7    | 2 (even) | 0 | 0 |

This snake pattern gives every player equal access to top picks across rounds.

### Live polling
```typescript
useEffect(() => {
  init()   // load everything once on mount
  const interval = setInterval(fetchPicks, 2000)  // then poll every 2 seconds
  return () => clearInterval(interval)             // cleanup on unmount
}, [roomCode, fetchPicks])
```

Polling every 2 seconds means when Player B makes a pick, Player A's screen
updates within 2 seconds without any action from Player A.

**Why not WebSockets?** WebSockets would give instant updates (server pushes to all
clients immediately). They're more complex to set up and require persistent
connections. Polling is simpler and works fine for a small group where 2-second
latency is acceptable.

---

## 13. Environment variables

**Why env variables?**

You don't want to hardcode `https://worlddraft.railway.app` in your frontend code:
1. It won't work locally (the local backend is at `localhost:8000`)
2. If you ever change the URL, you have to find and edit every file
3. You risk committing secrets (passwords, API keys) to git

The solution: the URL (or secret) lives in an environment variable that's set
differently in each environment.

**Frontend (Vite):**
Vite exposes variables prefixed with `VITE_` to the browser as `import.meta.env.VITE_*`.

```typescript
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
```

The `??` is the **nullish-coalescing operator**: if `VITE_API_URL` is `undefined`
(not set), fall back to `'http://localhost:8000'`. This means locally you don't
need to set anything — it just works.

Create a `frontend/.env.local` file (this is git-ignored):
```
VITE_API_URL=http://localhost:8000
```

In production (Vercel), you set `VITE_API_URL` to the Railway URL in the
Vercel dashboard.

**Backend (FastAPI):**
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/worlddraft")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
```

Same pattern — local fallback, production value set in Railway dashboard.

---

## 14. Deployment

### Why deploy at all?

If you just run the app on your laptop, it only works when your laptop is on and
connected to the internet. Your friends need to know your IP address. If the laptop
sleeps, the app goes offline. Deployment means running your app on a server in a
data center that's always on and has a permanent public URL.

### Backend: Railway

**What Railway does:**
- Reads your code from GitHub
- Installs dependencies from `requirements.txt`
- Reads `Procfile` to know how to start the server
- Runs your app on their servers 24/7
- Provides a managed PostgreSQL database
- Gives you a permanent URL like `worlddraft.railway.app`

**Why Railway and not AWS/Google Cloud?**
Railway is simpler. AWS and GCP have hundreds of services and complex pricing.
Railway has a free tier, a simple UI, and handles the infrastructure for you.

### `backend/Procfile`
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- `$PORT` is set by Railway — they choose which port to use
- `--host 0.0.0.0` means accept connections from any IP (not just localhost)
- Without this, your app would only be reachable from the same physical machine

### Frontend: Vercel

**What Vercel does:**
- Pulls your code from GitHub
- Runs `npm run build` which compiles TypeScript → JavaScript and bundles everything
- Hosts the resulting static files (HTML, JS, CSS) on a global CDN
- Gives you a permanent URL like `worlddraft.vercel.app`

**Why Vercel and not Railway for the frontend?**
After `npm run build`, the React app is just static files — no server needed. Vercel
is a specialized CDN (Content Delivery Network) for static files with servers in
dozens of cities worldwide. It's faster than a single Railway server and free for
small projects.

### `frontend/vercel.json`
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

React Router handles URLs like `/draft` and `/leaderboard` in JavaScript. But when
someone types `worlddraft.vercel.app/leaderboard` directly in their browser, Vercel's
file server looks for a file called `leaderboard` — which doesn't exist — and returns
a 404 error. This rewrite rule says "for any URL, serve `index.html`," letting
React Router handle the routing on the client side.

---

## 15. Deployment step-by-step

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOURNAME/worlddraft.git
git push -u origin main
```

### Step 2 — Deploy backend on Railway
1. Go to railway.app → sign up → New Project → Deploy from GitHub Repo
2. Select your `worlddraft` repository
3. In the service settings → **Root Directory**: set to `backend`
4. Railway detects the `Procfile` and starts your app
5. Add PostgreSQL: in your project → **+ New** → **Database** → **PostgreSQL**
6. Railway automatically injects `DATABASE_URL` into your backend service's env vars
7. In your backend service → **Variables**, add:
   - `FRONTEND_URL` = (leave blank for now, fill in after Step 3)
8. Your backend URL appears in the service's settings (e.g. `https://worlddraft-production.railway.app`)

### Step 3 — Deploy frontend on Vercel
1. Go to vercel.com → sign up → New Project → Import Git Repository
2. Select `worlddraft`
3. Configure the project:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Under **Environment Variables**, add:
   - `VITE_API_URL` = your Railway backend URL from Step 2
5. Click Deploy
6. Vercel gives you a URL like `https://worlddraft.vercel.app`

### Step 4 — Wire them together
1. Back in Railway → your backend service → **Variables**
2. Set `FRONTEND_URL` = your Vercel URL (e.g. `https://worlddraft.vercel.app`)
3. Railway automatically redeploys with the new variable

### Step 5 — Seed teams into the production database
Your production PostgreSQL is empty. You need to insert the 48 World Cup teams.
Options:
- Write a seed script (`backend/app/seed_teams.py`) and run it via
  `railway run python -m app.seed_teams`
- Or temporarily expose an admin endpoint that inserts the teams, call it once, then remove it
- Or connect to the Railway PostgreSQL directly via a GUI like pgAdmin or TablePlus
  and run INSERT statements

### Step 6 — Test the live app
1. Visit your Vercel URL
2. Register an account
3. Join a room code (make one up, e.g. `WORLD26`)
4. Open another browser / incognito window, register a second account, join same room
5. Confirm the draft grid shows both players and turns advance correctly
6. Click "Refresh from FIFA" on the leaderboard to sync live results

---

## 16. Full tech stack summary

| Layer | Technology | Why we chose it |
|-------|-----------|-----------------|
| Database | PostgreSQL | Reliable, relational, free, Railway managed |
| ORM | SQLAlchemy | Pythonic DB access, auto table creation |
| API framework | FastAPI | Fast to write, auto docs, type-safe |
| API server | Uvicorn | ASGI server, production-grade |
| Request validation | Pydantic | Automatic JSON validation, Python types |
| Frontend build | Vite | Fast dev server, modern build tooling |
| UI framework | React 19 | Component model, large ecosystem |
| Type system | TypeScript | Catch bugs before running code |
| Routing | React Router v6 | Client-side navigation |
| Backend host | Railway | Simple, free tier, includes Postgres |
| Frontend host | Vercel | Optimized for static/SPA frontends, free |

---

## 17. Concepts to learn next

These are the natural next steps after building this project:

| Concept | What it is | Why it matters |
|---------|-----------|----------------|
| Password hashing | bcrypt/argon2 — one-way fingerprint of a password | Never store plain-text passwords in a real app |
| JWT tokens | Signed tokens the server issues on login | Stateless auth — server doesn't need a session table |
| WebSockets | Persistent two-way connection | Real-time push instead of polling |
| React Query / SWR | Libraries for data fetching + caching | Makes `useEffect` + `fetch` patterns cleaner |
| Alembic | Database migration tool | Change table schemas without dropping data |
| Docker | Package app + dependencies into a container | "Works on my machine" problems disappear |
| GitHub Actions | CI/CD — run tests and deploy on every push | Catches bugs before they reach production |
| HTTPS / TLS | Encrypts traffic between browser and server | Railway and Vercel handle this for you automatically |
| Rate limiting | Reject too-many requests from one IP | Prevents abuse of your API |
| Indexes explained | How `index=True` speeds up queries | B-trees, query planning, when to add/avoid indexes |
