# Run CalNode

First edit .env and client_secrets.json in the secrets folder.

Run without docker in python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn calnode.api:app --host 0.0.0.0 --port 8080
```

Run with docker:

```bash
docker build -t calnode .
docker compose up -d
```