# Healthcare Backend (Django + DRF + PostgreSQL + JWT)

REST API for registering users and managing patients, doctors and patient–doctor assignments.


A REST backend for a healthcare application. Users can register and log in (JWT), manage **patients** and
**doctors**, and assign doctors to patients.

**Stack:** Python · Django 5 · Django REST Framework · PostgreSQL · JWT (`djangorestframework-simplejwt`)

---

## Contents

1. [Features](#1-features)
2. [Prerequisites](#2-prerequisites)
3. [Setup](#3-setup)
4. [Run the server](#4-run-the-server)
5. [How to verify the project (for reviewers)](#5-how-to-verify-the-project-for-reviewers)
6. [API reference](#6-api-reference)
7. [Environment variables](#7-environment-variables)
8. [Project structure](#8-project-structure)
9. [Design decisions](#9-design-decisions)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Features

- Register and log in with email + password; login returns JWT access and refresh tokens.
- Full CRUD for patients (private to the user who created them) and doctors (shared, editable by creator only).
- Patient-doctor assignments (mappings) with duplicate and ownership protection.
- Validation on every input and one consistent JSON error format.
- Secrets and database settings come from environment variables (`.env`), never from code.
- Automated tests (37) and an importable Postman collection (24 requests, 32 assertions).

---

## 2. Prerequisites

| Requirement | Version | Check with |
|---|---|---|
| Python | 3.10 or newer | `python --version` |
| PostgreSQL | 13 or newer | `psql --version` |
| Git | any | `git --version` |

Python packages (installed from `requirements.txt`):

| Package | Purpose |
|---|---|
| Django (>=5.0, <5.2) | Web framework / ORM |
| djangorestframework | REST API |
| djangorestframework-simplejwt | JWT authentication |
| psycopg2-binary | PostgreSQL driver |
| python-decouple | Reads settings from `.env` |

---

## 3. Setup

Run all commands from the project root (the folder that contains `manage.py`).

### Step 1: Create the database

Open `psql` (or pgAdmin) and run:

```sql
CREATE DATABASE healthcare_db;
```

Command-line version: `psql -U postgres -c "CREATE DATABASE healthcare_db;"`

### Step 2: Create a virtual environment and install dependencies

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure environment variables

Copy the example file and edit it:

```powershell
copy .env.example .env      # Windows
```
```bash
cp .env.example .env        # macOS / Linux
```

Open `.env` and set at least:

- `SECRET_KEY`: any long random string. Generate one with:
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DB_PASSWORD`: your PostgreSQL password

The other values work as they are if PostgreSQL runs locally on the default port. Full list in
[Environment variables](#7-environment-variables).

### Step 4: Create the tables

```bash
python manage.py migrate
```

Migrations are already included in the repository, so `makemigrations` is **not** needed.

### Optional: admin user

```bash
python manage.py createsuperuser
```
Then log in at http://127.0.0.1:8000/admin/ to browse the data.

---

## 4. Run the server

```bash
python manage.py runserver
```

Base URL: **http://127.0.0.1:8000/**
Opening it in a browser should show `{"message": "Healthcare API is running", ...}`.

---

## 5. How to verify the project (for reviewers)

Pick any of the three options. Option A takes about two minutes once the server is running.

### Option A: Postman collection (recommended)

1. Start the server (section 4).
2. In Postman press `Ctrl + O` (Import) and choose `postman/Healthcare_API.postman_collection.json`.
3. Open the collection, click **Run**, then **Start run**.
4. All 24 requests should pass (32 assertions).

The collection registers a fresh user on every run, stores the JWT automatically, and also checks error
cases (wrong password, invalid data, duplicate email, missing token, unknown id).
Change the `base_url` collection variable if the server is not on `127.0.0.1:8000`.

### Option B: Automated tests

```bash
python manage.py test
```

Expected: `Ran 37 tests ... OK` (about 1 minute; password hashing is intentionally slow).
The PostgreSQL user in `.env` must be allowed to create databases (the default `postgres` user is).
Django creates a temporary `test_healthcare_db` and removes it afterwards.

### Option C: Manual walkthrough

**Windows PowerShell**
```powershell
$base = "http://127.0.0.1:8000"
$json = "application/json"

# 1. Register
Invoke-RestMethod -Method Post -Uri "$base/api/auth/register/" -ContentType $json `
  -Body '{"name":"Asha","email":"asha@example.com","password":"Str0ngPass!23"}'

# 2. Login and keep the token
$login = Invoke-RestMethod -Method Post -Uri "$base/api/auth/login/" -ContentType $json `
  -Body '{"email":"asha@example.com","password":"Str0ngPass!23"}'
$h = @{ Authorization = "Bearer $($login.access)" }

# 3. Create a patient and a doctor
Invoke-RestMethod -Method Post -Uri "$base/api/patients/" -Headers $h -ContentType $json `
  -Body '{"name":"Ravi","age":30,"gender":"male"}'
Invoke-RestMethod -Method Post -Uri "$base/api/doctors/" -Headers $h -ContentType $json `
  -Body '{"name":"Meera","specialization":"Cardiology","email":"meera@example.com","experience_years":8}'

# 4. Assign doctor 1 to patient 1, then list the patient's doctors
Invoke-RestMethod -Method Post -Uri "$base/api/mappings/" -Headers $h -ContentType $json -Body '{"patient":1,"doctor":1}'
Invoke-RestMethod -Uri "$base/api/mappings/1/" -Headers $h | ConvertTo-Json -Depth 5
```

**macOS / Linux (curl)**
```bash
BASE=http://127.0.0.1:8000

curl -s -X POST $BASE/api/auth/register/ -H "Content-Type: application/json" \
  -d '{"name":"Asha","email":"asha@example.com","password":"Str0ngPass!23"}'

TOKEN=$(curl -s -X POST $BASE/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"asha@example.com","password":"Str0ngPass!23"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")

curl -s -X POST $BASE/api/patients/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Ravi","age":30,"gender":"male"}'
curl -s $BASE/api/patients/ -H "Authorization: Bearer $TOKEN"
```

> Note: every URL must end with `/`. A POST without the trailing slash returns a 500 error in Django.

---

## 6. API reference

All endpoints except register and login need the header `Authorization: Bearer <access_token>`.

### Authentication

| Method | Endpoint | Body | Success |
|---|---|---|---|
| POST | `/api/auth/register/` | `name`, `email`, `password` | 201 |
| POST | `/api/auth/login/` | `email`, `password` | 200 with `access` and `refresh` |
| POST | `/api/auth/token/refresh/` | `refresh` | 200 with new `access` |

Passwords must pass Django's validators (min 8 characters, not too common, not all numeric).
The access token lives 60 minutes by default (configurable).

### Patients (each user sees only their own)

| Method | Endpoint | Notes | Success |
|---|---|---|---|
| POST | `/api/patients/` | `name`, `age`, `gender` (`male`/`female`/`other`); optional `phone`, `address`, `medical_history` | 201 |
| GET | `/api/patients/` | Patients created by you | 200 |
| GET | `/api/patients/<id>/` | | 200 |
| PUT | `/api/patients/<id>/` | Full update (PATCH also works) | 200 |
| DELETE | `/api/patients/<id>/` | | 204 |

### Doctors (everyone can read; only the creator can edit or delete)

| Method | Endpoint | Notes | Success |
|---|---|---|---|
| POST | `/api/doctors/` | `name`, `specialization`, `email` (unique); optional `phone`, `experience_years` | 201 |
| GET | `/api/doctors/` | All doctors | 200 |
| GET | `/api/doctors/<id>/` | | 200 |
| PUT | `/api/doctors/<id>/` | Creator only (others get 403) | 200 |
| DELETE | `/api/doctors/<id>/` | Creator only (others get 403) | 204 |

### Patient-doctor mappings

| Method | Endpoint | Notes | Success |
|---|---|---|---|
| POST | `/api/mappings/` | `{"patient": <id>, "doctor": <id>}`. Patient must be yours; duplicates rejected | 201 |
| GET | `/api/mappings/` | All mappings for your patients | 200 |
| GET | `/api/mappings/<patient_id>/` | Doctors assigned to that patient (with full doctor details) | 200 |
| DELETE | `/api/mappings/<id>/` | `<id>` is the **mapping** id returned when assigning | 204 |

`GET /api/mappings/<patient_id>/` and `DELETE /api/mappings/<id>/` share a URL shape, as specified in the
assignment: the first takes a patient id, the second a mapping id.

### Status codes and error format

| Code | Meaning |
|---|---|
| 400 | Validation error (bad or missing fields, duplicates) |
| 401 | Missing, invalid or expired token |
| 403 | Authenticated but not allowed (e.g. editing another user's doctor) |
| 404 | Not found (also returned for other users' patients and mappings) |

Every error has the same shape:

```json
{"error": {"status_code": 400, "message": "Validation failed.", "details": {"email": ["A user with this email already exists."]}}}
```

---

## 7. Environment variables

Defined in `.env` (copy from `.env.example`). `.env` is git-ignored and must never be committed.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | yes | none | Django secret key |
| `DEBUG` | no | `False` | `True` for local development only |
| `ALLOWED_HOSTS` | no | `localhost,127.0.0.1` | Comma-separated hosts |
| `DB_NAME` | yes | none | PostgreSQL database name (`healthcare_db`) |
| `DB_USER` | yes | none | PostgreSQL user (e.g. `postgres`) |
| `DB_PASSWORD` | yes | none | PostgreSQL password |
| `DB_HOST` | no | `localhost` | Database host |
| `DB_PORT` | no | `5432` | Database port |
| `ACCESS_TOKEN_MINUTES` | no | `60` | JWT access token lifetime |
| `REFRESH_TOKEN_DAYS` | no | `7` | JWT refresh token lifetime |

---

## 8. Project structure

```
healthcare_backend/
├── manage.py
├── requirements.txt
├── .env.example               # template for .env
├── .gitignore
├── README.md
├── config/                    # project settings
│   ├── settings.py            # reads .env, DRF + JWT + PostgreSQL config
│   ├── urls.py                # root routes and health check
│   ├── exceptions.py          # consistent JSON error responses
│   └── testing.py             # shared helpers for tests
├── accounts/                  # register, login (JWT)
├── patients/                  # Patient model, serializer, views
├── doctors/                   # Doctor model, serializer, views, permissions
├── mappings/                  # PatientDoctorMapping model, serializer, views
└── postman/
    └── Healthcare_API.postman_collection.json
```

Each app contains `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `tests.py` and `migrations/`.

---

## 9. Design decisions

- **Email is the login.** The email is stored in Django's `username` field (lower-cased), so login is email + password without a custom user model.
- **Patients are private.** A user can only list, read, change or delete patients they created. Other users get 404, which does not reveal that the record exists.
- **Doctors are shared.** Any logged-in user can read every doctor, but only the creator can edit or delete.
- **Mappings are protected.** You can only assign doctors to your own patients. The same doctor cannot be assigned to a patient twice (validation plus a database unique constraint).
- **Cascade deletes.** Deleting a patient or doctor removes its mappings.
- **Consistent errors.** A custom exception handler wraps all DRF errors in one JSON structure.
- **Secrets stay out of code.** All sensitive and environment-specific settings are read from `.env`.

---

## 10. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `decouple.UndefinedValueError: SECRET_KEY not found` | `.env` is missing. Copy `.env.example` to `.env` and fill it in. |
| `password authentication failed for user` | `DB_PASSWORD` in `.env` does not match your PostgreSQL password. |
| `connection refused` / `could not connect to server` | PostgreSQL is not running, or `DB_HOST` / `DB_PORT` is wrong. |
| `database "healthcare_db" does not exist` | Create it first (Setup, step 1). |
| `permission denied to create database` when running tests | The `DB_USER` needs the CREATEDB privilege (the `postgres` user has it). |
| `401 ... token_not_valid / Token is expired` | Access tokens last 60 minutes. Log in again, or use `/api/auth/token/refresh/`. |
| `500` with `doesn't end in a slash` on POST | Add the trailing `/` to the URL (`/api/patients/`, not `/api/patients`). |
| `pip install psycopg2-binary` fails | Upgrade pip (`python -m pip install --upgrade pip`) and use a supported Python version (3.10+). |
| `404` on `http://127.0.0.1:8000/some-page` | Only `/`, `/admin/` and `/api/...` routes exist. |
