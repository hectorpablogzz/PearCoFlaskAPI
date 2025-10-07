# PearCo. Flask API

API meant to be used with PearCoProject: https://github.com/hectorpablogzz/PearCoProject

## Requirements

- Python 3.12  
- `pip` or `uv`  
- Docker *(optional for container builds)*  

---


## API Endpoints (Production)

**Base URL:**  
`https://pearcoflaskapi.onrender.com`

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `GET` | `/` | Health check (optional `?who=CafeCare`) |
| `GET` | `/reports` | Returns disease probability reports in JSON |
| `GET` | `/summary` | Returns aggregated summary JSON |
| `GET` | `/caficultores` | Returns farmer profiles in JSON |
| `POST` | `/caficultores` | Adds a farmer to the database |
| `PUT` | `/caficultores/<id>` | Edits a farmer in the database |
| `DELETE` | `/caficultores/<id>` | Deletes a farmer from the database |

Example:  
```bash
curl https://pearcoflaskapi.onrender.com/summary
```

---

## Deployment (API on Render)

If the API is already live, skip this section.  
To redeploy or fork it under another account:

### Prerequisites
Your repo must include:
- `app.py` (Flask app exposing `/`, `/reports`, `/summary`)
- `Dockerfile`
- `requirements.txt` *(recommended)*

### Example Dockerfile
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
ENV PORT=8000

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app
EXPOSE 8000

# Flask app exposed as "app:app"
CMD ["sh","-c","flask run --host=0.0.0.0 --port=${PORT}"]
```

### Example requirements.txt
```
flask==3.0.0
# Add any libraries used for reports or data processing
```

### Steps to Deploy
1. Push your repo to GitHub.  
2. Go to [Render](https://render.com).  
3. Click **New + → Web Service**.  
4. Choose your repo and select **Docker** runtime (auto-detected).  
5. Choose the **Free Plan**.  
6. Wait for build → once live, test your endpoints:
   - `https://<your-service>.onrender.com/`
   - `https://<your-service>.onrender.com/reports`
   - `https://<your-service>.onrender.com/summary`
