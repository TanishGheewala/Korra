# Project 11: Korra Human in the Loop


## Run

```powershell
docker compose up --build -d --wait
docker compose exec korra python demo.py before
docker compose down
docker compose up -d --wait
docker compose exec korra python demo.py after
```

## Other commands

```powershell
docker compose exec korra python korra.py students
docker compose exec korra python korra.py pending
docker compose exec korra python korra.py audit
docker compose exec korra python korra.py propose sample.json
docker compose exec korra python korra.py review DECISION_ID
```
