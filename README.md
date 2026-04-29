# Qatar Foundation - Admin Portal(Backend)

> Built as part of the CertifyMe Full Stack Intern Assessment.
> Task: Connect a pre-built Admin UI to a fully functional Flask backend
> with authentication, session management, and opportunity management.

---

## What I built

The frontend (HTML/CSS/JS) was already provided. My job was to build the entire backend from scratch and wire it to the existing UI without changing a single line of the frontend design. This meant understanding what the UI expected what form fields it sent, what JSON shape it needed back, how it stored tokens and building an API that matched that contract exactly.

---

## How the system works

### Authentication flow
When an admin signs up, their password is hashed with bcrypt before being stored the plain text password never touches the database.
On login, the server verifies the password hash and returns a signed JWT. The frontend stores this token in localStorage (if Remember Me is checked) or sessionStorage (if not) - this is how the "session ends when browser closes" behaviour is achieved without any server-side session management.
Every protected endpoint reads this token from the Authorization header, verifies the signature, and extracts the admin's ID from the payload. This means the server is fully stateless no sessions, no cookies, no server-side state.

### Why the login error is generic
The login endpoint returns "Invalid email or password" for both a wrong email AND a wrong password. This is intentional. If the error said "email not found", an attacker could use the login form to check whether any email address is registered in the system. Using the same message for both cases prevents this - it's called preventing user enumeration.

### Why forgot password always succeeds
The forgot password endpoint always returns the same success message regardless of whether the email exists in the database. This protects user privacy if it returned an error for unknown emails, anyone could check whether a person has an account on the platform.
The reset link is generated and printed to the terminal as specified in US-1.3. In production this would be sent via Flask-Mail or SendGrid. The token expires after 1 hour and is single-use.

### Admin data isolation
Every opportunity is stored with an `admin_id` foreign key pointing to the admin who created it. Every single read, update, and delete endpoint checks that the `admin_id` of the record matches the ID from the JWT. This means admins are completely isolated they cannot read, edit, or delete each other's data even if they know the ID of another admin's opportunity.
This check is on every endpoint, not just delete. Most implementations only protect delete - I protected all of them.

---

## Project structure
```
admin-portal/
├── sky/                        # Pre-built frontend (not modified)
│   ├── admin.html
│   ├── admin.css
│   ├── admin.js                # Existing JS + API wiring added
│   └── api.js                  # New file - all fetch calls live here
│
└── backend/
    ├── app.py                  # App factory, CORS, blueprint registration
    ├── models.py               # SQLAlchemy models - Admin, Opportunity, ResetToken
    ├── blueprints/
    │   ├── auth.py             # Signup, login, forgot password
    │   └── opportunities.py   # Full CRUD + auth middleware
    ├── requirements.txt
    ├── .env.example
    └── postman_collection.json
```
---

## Tech stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | Flask 3.0 | Lightweight, matches assignment spec |
| Database | SQLite via SQLAlchemy | Zero config for local dev, easy to swap to Postgres |
| Password hashing | bcrypt | Industry standard, slow by design to resist brute force |
| Session tokens | PyJWT (HS256) | Stateless auth, no server-side session storage needed |
| CORS | Flask-CORS | Allows the frontend served on the same origin to call the API |

---

## Setup

#### 1. Clone the repo
```
git clone https://github.com/Bhakthi-Shetty7811/admin-portal.git
cd admin-portal
```

#### 2. Move into backend
```
cd backend
```

#### 3. Create and activate virtual environment
```
python -m venv venv
```

#### Mac/Linux:
```
source venv/bin/activate
```

#### Windows:
```
venv\Scripts\activate
```

#### 4. Install dependencies
```
pip install -r requirements.txt
```

#### 5. Create your .env file
```
cp .env.example .env
```

#### Open .env and replace the placeholder values with real secrets.
#### Generate them with:
```
python -c "import secrets; print(secrets.token_hex(32))"
```
#### Run this twice - once for SECRET_KEY, once for JWT_SECRET.

#### 6. Start the server
```
python app.py
```

Open `http://localhost:5000` - the admin portal loads directly.
SQLite database is created automatically on first run.

---

## API reference

### Auth endpoints (no token required)

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/signup | Register new admin - bcrypt hashes password before saving |
| POST | /api/login | Verify credentials - returns signed JWT on success |
| POST | /api/forgot-password | Generate reset token - always returns success (privacy) |
| GET | /api/reset-password/:token | Validate a reset link - returns error if expired or used |

### Opportunity endpoints (JWT required)

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/opportunities | List all opportunities for the logged-in admin only |
| POST | /api/opportunities | Create a new opportunity linked to logged-in admin |
| GET | /api/opportunities/:id | Get one opportunity - 404 if belongs to another admin |
| PUT | /api/opportunities/:id | Update - ownership verified before any change |
| DELETE | /api/opportunities/:id | Delete - ownership verified, 404 if not yours |

All protected endpoints read `Authorization: Bearer <token>` from the
request header. Missing or invalid tokens return `401`.

---

## Security decisions

**Passwords** - hashed with bcrypt before storage. The plain text password is never written to the database or logged anywhere.

**JWT tokens** - signed with HS256. Payload contains admin ID and expiry. Token is verified on every protected request no database lookup needed to authenticate, keeping the server stateless.

**Remember Me** - implemented via token expiry. Checked = 30 day token stored in localStorage. Unchecked = 8 hour token stored in sessionStorage, which clears when the browser closes.

**User enumeration protection** - login returns the same error for wrong email and wrong password. An attacker cannot use the login form to discover which email addresses are registered.

**Privacy-safe password reset** - forgot password always returns success. The reset link is only generated if the email exists, but the response never reveals whether it does.

**Admin data isolation** - every opportunity endpoint checks `opportunity.admin_id == current_admin.id`. Even if an attacker has a valid JWT, they cannot read or modify another admin's data. The response is a 404 (not 403) to avoid confirming the record exists.

**Reset token expiry** - tokens are UUID-based, stored with an `expires_at` timestamp, and marked `used=True` after one use. Expired or used tokens return a clear error message.

---

## Forgot password - dev behaviour

As specified in US-1.3, no email is sent. The reset link is printed to the Flask terminal when the endpoint is called:

```
[DEV] Password reset link for admin@example.com:
  http://localhost:5000/api/reset-password/1ed8d9bf52f94492adb2df9a538f9a2a
```

In production this line would be replaced with a call to Flask-Mail or an email service like SendGrid.

---

## User stories coverage

| Story | Title | Status |
|---|---|---|
| US-1.1 | Admin Sign Up | ✅ Complete |
| US-1.2 | Admin Login | ✅ Complete |
| US-1.3 | Forgot Password | ✅ Complete |
| US-2.1 | View All Opportunities | ✅ Complete |
| US-2.2 | Add New Opportunity | ✅ Complete |
| US-2.3 | Opportunities Persist After Login | ✅ Complete |
| US-2.4 | View Opportunity Details | ✅ Complete |
| US-2.5 | Edit Opportunity | ✅ Complete |
| US-2.6 | Delete Opportunity | ✅ Complete |

---

## Demo video
[Watch 2-minute walkthrough](https://drive.google.com/file/d/17mHFiNjJuvMOzsLqWjHvjZypNUCrhDvy/view?usp=sharing)

The demo covers: signup → login → create opportunity → edit → delete → logout → login again (proves persistence) → forgot password with terminal reset link shown.
```
