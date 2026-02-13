# Backend (FastAPI)

## Start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run worker:

```bash
python worker.py
```

If a site needs browser rendering (`parser_rules.use_browser=true`):

```bash
playwright install chromium
```

Default seeded admin account:

- username: `admin`
- password: `admin123456`
