# Sky Foundation Admin Portal — Backend

Flask REST API for the Universal Skills Passport admin dashboard.

## Tech stack
- Python 3.11+
- Flask 3.0
- SQLAlchemy (SQLite for dev)
- bcrypt (password hashing)
- PyJWT (session tokens)
- Flask-CORS

## Setup

```bash
# 1. Clone the repo (frontend is already in sky/)
git clone https://github.com/Neerajvs32/Test1

# 2. Move into the backend folder
cd backend

# 3. Create a virtual environment
python -m venv venv

# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create your .env file
cp .env.example .env
# Then open .env and replace the placeholder secrets with real random strings.
# Generate them: python -c "import secrets; print(secrets.token_hex(32))"

# 6. Run the server
python app.py
```

The server starts at http://localhost:5000.
Open http://localhost:5000 in your browser to see the admin portal.

## API endpoints

| Method | Endpoint | Auth? | Description |
|--------|----------|-------|-------------|
| POST | /api/signup | No | Register a new admin |
| POST | /api/login | No | Login, returns JWT |
| POST | /api/forgot-password | No | Request password reset |
| GET | /api/reset-password/:token | No | Validate reset token |
| GET | /api/opportunities | Yes | List logged-in admin's opportunities |
| POST | /api/opportunities | Yes | Create a new opportunity |
| GET | /api/opportunities/:id | Yes | Get single opportunity |
| PUT | /api/opportunities/:id | Yes | Edit an opportunity |
| DELETE | /api/opportunities/:id | Yes | Delete an opportunity |

## Security decisions
- Passwords are bcrypt-hashed (never stored in plain text)
- JWTs are signed with HS256 and include expiry
- Login returns the same error whether the email or password is wrong (prevents user enumeration)
- Forgot password always returns success (protects user privacy)
- Every opportunity write checks `admin_id == current_admin.id` (admins cannot touch each other's data)
- Reset tokens expire after 1 hour and are single-use

### Forgot password
The reset link is printed to the Flask terminal (as specified in US-1.3 no email sending required at this stage). In production this would be sent via Flask-Mail or SendGrid.