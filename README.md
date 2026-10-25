# CodeAlpha_DataRedundancyRemoval

A cloud-ready system that decides whether incoming data is **UNIQUE**, **REDUNDANT** or a **FALSE POSITIVE**, and only appends unique, verified records to the database.

Built for the **CodeAlpha Cloud Computing Internship (Task 1)**.

> Live demo: _add the EC2 URL here after deployment_
> Video walkthrough: _add the LinkedIn video link here_

## Features

- Validation of every field (name, email, phone, city) with clear reasons for rejection
- Normalization: lowercase names, Gmail dot/plus-tag removal, unified Pakistani phone formats
- SHA-256 fingerprint of each cleaned record
- Three verdicts: `UNIQUE` (saved), `REDUNDANT` (duplicate), `FALSE_POSITIVE` (invalid or fake data)
- Two layers of duplicate protection: application check + database `UNIQUE` keys (safe even in race conditions)
- Audit log of every submission, accepted or rejected
- Single-page UI with live statistics, stored records and recent activity
- Health endpoint for cloud monitoring
- 57 automated tests, written test-first

## How a record is classified

1. Validation fails -> `FALSE_POSITIVE` (stored only in `audit_log`)
2. Normalized email already exists -> `REDUNDANT`
3. Normalized phone exists **and** name similarity >= 0.85 -> `REDUNDANT`
4. Database `UNIQUE` key rejects the insert (simultaneous requests) -> `REDUNDANT`
5. Otherwise -> `UNIQUE`, inserted into `records`

Same phone with a clearly different name is allowed on purpose (family members can share a phone).

## Architecture

```
Browser (HTML + CSS + JS, fetch/AJAX)
        |  JSON
        v
Flask app (EC2, gunicorn)
  routes.py -> services.py -> classifier.py -> validators.py
        |  prepared statements (PyMySQL)
        v
MySQL (RDS, private): records (UNIQUE email_norm, fingerprint) + audit_log
```

| File | Responsibility |
|------|----------------|
| `app/validators.py` | Field validation, returns reasons |
| `app/classifier.py` | Normalize, fingerprint, decide verdict (pure functions, no DB) |
| `app/services.py` | Database work: lookup, insert, audit log |
| `app/routes.py` | HTTP endpoints |
| `app/config.py` / `app/db.py` | Settings from environment, one place to open connections |
| `sql/schema.sql` | Database and tables |

## Tech stack

Python 3, Flask, MySQL (AWS RDS in the cloud, XAMPP locally), PyMySQL, HTML/CSS/JavaScript, pytest, Gunicorn, AWS EC2 + RDS.

## API

| Method | Path | Purpose | Status codes |
|--------|------|---------|--------------|
| GET | `/` | Web page | 200 |
| GET | `/health` | App + database check | 200 / 503 |
| POST | `/api/records` | Submit a record (JSON) | 201 unique, 409 redundant, 422 false positive, 400 bad JSON |
| GET | `/api/records` | Stored unique records | 200 |
| GET | `/api/audit` | Recent submissions | 200 |
| GET | `/api/stats` | Counters | 200 |

Example body: `{"full_name": "Ali Khan", "email": "ali@example.com", "phone": "0300-1234567", "city": "Faisalabad"}`

## Run locally (Windows)

1. Install Python 3.11+, Git, and XAMPP (start MySQL).
2. Clone the repo and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install Flask PyMySQL python-dotenv pytest
   ```
3. Create the database:
   ```
   cmd /c "C:\xampp\mysql\bin\mysql.exe -u root < sql\schema.sql"
   ```
4. Copy the settings file and edit it if your MySQL has a password:
   ```
   Copy-Item .env.example .env
   ```
5. Start the app and open http://127.0.0.1:5000/
   ```
   python wsgi.py
   ```

On a server (EC2) use `pip install -r requirements.txt` and `gunicorn wsgi:app`.

## Run the tests

```
python -m pytest -v
```

## Security choices

- **Prepared statements** for every SQL query (no SQL injection)
- **No secrets in code**: settings come from environment variables; `.env` is git-ignored
- **Output escaping**: the UI uses `textContent`, never `innerHTML`
- **Input validation** before anything touches the database
- **Private database** on AWS: RDS is reachable only from the app server's security group

## Known limitations

- Phone length (30) is defined in both the validator and the database column; change both together.
- Gmail dot/plus normalization is applied only to Gmail addresses.
- Single-server design; heavy traffic needs a load balancer and auto scaling (see Task 3).
- No login system, bulk import or fuzzy matching beyond name similarity.

## Screenshots

_Add screenshots to `docs/screenshots/` and link them here._

## Author

Muhammad Akram - CodeAlpha Cloud Computing Intern