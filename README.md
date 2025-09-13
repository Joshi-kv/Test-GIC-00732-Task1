# Django File Uploader + Rate Limiting

A simple Django REST API that lets you upload CSV files and protects the API with a Redis-backed rate limiter.

## Features
- **CSV upload endpoint** with validation
- **Global IP-based rate limiting** using Redis
- **Clear response headers** for rate limits: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- **Unit tests** for uploader and rate limit behavior

## Tech Stack
- Django 5
- Django REST Framework
- Redis (via `django-redis`)
- SQLite (dev default)

## Project Structure (high level)
```
core/                           # Project settings, URLs, middleware
  middlewares/rate_limiting_middleware.py
api/
  urls.py                       # v1 endpoints (upload-file)
  v1/views/uploader.py          # FileUploadView
models/                         # Example app
scripts/create_csv.py           # Utility to generate a sample CSV
```

## Quickstart
1) Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Start Redis locally
- Default Redis URL in settings: `redis://127.0.0.1:6379/1`
- Make sure Redis is running: `redis-server` (or via Docker)

Docker example:
```bash
docker run -p 6379:6379 --name redis -d redis:7
```

4) Apply migrations
```bash
python manage.py migrate
```

5) Run the server
```bash
python manage.py runserver
```

## API
Base URL (dev): `http://127.0.0.1:8000/`

- POST `v1/api/upload-file/`
  - Description: Upload a CSV file.
  - Form field: `file` (multipart/form-data)
  - Success: `201 Created`
  - Rate Limit headers (on every response):
    - `X-RateLimit-Limit`: max requests per window
    - `X-RateLimit-Remaining`: remaining requests in the current window
    - `Retry-After`: seconds until the window resets (present when limited)

Example curl:
```bash
curl -X POST \
  -F "file=@test_files/test_data.csv" \
  http://127.0.0.1:8000/api/upload-file/
```

## Rate Limiting
- Middleware: `core.middlewares.rate_limiting_middleware.RateLimitMiddleware`
- Defaults (see `core/settings.py`):
  - `RATE_LIMIT = 100` requests
  - `RATE_LIMIT_TIME_PERIOD = 300` seconds
- Uses Redis with per-IP keys. When exceeded, returns `429 Too Many Requests` with `Retry-After`.

To change the limits, update in `core/settings.py`:
```python
RATE_LIMIT = 10
RATE_LIMIT_TIME_PERIOD = 60
```

## Running Tests
```bash
python manage.py test

# To run specific tests
python manage.py test tests.test_uploader
python manage.py test tests.test_rate_limit

```

## Troubleshooting
- Redis not running: You’ll see errors or unlimited requests. Start Redis and retry.
- Headers missing: Ensure the middleware is in `MIDDLEWARE` and Redis cache is configured.
- 429 too soon: You might be sharing an IP (e.g., via proxy). Adjust limits for local testing.

