# Game Item Trading API

A REST API service built with **Python + FastAPI** for trading in-game items between users.

## Features

- **User Registration & Login** – JWT-based authentication
- **User Profiles** – View / update profile, change password
- **Item Management** – Create, list, search, filter, update, and delete in-game items
- **Swap System** – Propose, accept, reject, cancel item swaps
- **Rating System** – Rate completed swaps (1-5 stars + optional review)
- **Swap History** – View past swaps with status filtering

## Quick Start

### 1. Install Dependencies

```bash
cd game-item-trading-api
python -m venv venv
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**

### 3. Interactive Docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
game-item-trading-api/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (env vars / .env)
│   ├── database.py          # SQLAlchemy engine & session
│   ├── dependencies.py      # Auth dependency (get_current_user)
│   ├── models/
│   │   ├── user.py          # User ORM model
│   │   ├── item.py          # Item ORM model
│   │   └── swap.py          # Swap ORM model + association tables
│   ├── schemas/
│   │   ├── user.py          # User Pydantic schemas
│   │   ├── item.py          # Item Pydantic schemas
│   │   └── swap.py          # Swap Pydantic schemas
│   ├── routers/
│   │   ├── auth.py          # POST /register, /login
│   │   ├── users.py         # GET/PUT /users/me, GET /users/{id}
│   │   ├── items.py         # CRUD + search for items
│   │   └── swaps.py         # Propose/accept/reject/rate swaps
│   └── utils/
│       └── security.py      # Password hashing & JWT helpers
├── requirements.txt
└── README.md
```

## API Endpoints

### Authentication
| Method | Endpoint             | Description           | Auth |
|--------|----------------------|-----------------------|------|
| POST   | `/api/auth/register` | Register new user     | No   |
| POST   | `/api/auth/login`    | Login, get JWT token  | No   |

### Users
| Method | Endpoint              | Description                  | Auth |
|--------|-----------------------|------------------------------|------|
| GET    | `/api/users/me`       | Get current user profile     | Yes  |
| PUT    | `/api/users/me`       | Update profile               | Yes  |
| PUT    | `/api/users/me/password` | Change password           | Yes  |
| GET    | `/api/users/{id}`     | Get public user profile      | No   |

### Items
| Method | Endpoint             | Description                        | Auth |
|--------|----------------------|------------------------------------|------|
| POST   | `/api/items/`        | Create a new item                  | Yes  |
| GET    | `/api/items/`        | List/search items (with filters)   | No   |
| GET    | `/api/items/my`      | List own items                     | Yes  |
| GET    | `/api/items/{id}`    | View item details                  | No   |
| PUT    | `/api/items/{id}`    | Update own item                    | Yes  |
| DELETE | `/api/items/{id}`    | Delete own item                    | Yes  |

### Swaps
| Method | Endpoint                     | Description                | Auth |
|--------|------------------------------|----------------------------|------|
| POST   | `/api/swaps/`                | Propose a swap             | Yes  |
| GET    | `/api/swaps/history`         | List your swap history     | Yes  |
| GET    | `/api/swaps/{id}`            | Get swap details           | Yes  |
| POST   | `/api/swaps/{id}/accept`     | Accept a swap              | Yes  |
| POST   | `/api/swaps/{id}/reject`     | Reject a swap              | Yes  |
| POST   | `/api/swaps/{id}/cancel`     | Cancel your own swap       | Yes  |
| POST   | `/api/swaps/{id}/rate`       | Rate a completed swap      | Yes  |

## Configuration

Create a `.env` file in the project root to override defaults:

```env
SECRET_KEY=your-super-secret-key
DATABASE_URL=sqlite:///./trading.db
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## License

MIT
