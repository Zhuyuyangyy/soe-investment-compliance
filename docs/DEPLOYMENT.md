# Deployment Guide

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- 512MB+ RAM
- 1GB+ disk space

## Local Development

### 1. Clone and Setup

```bash
git clone <repository-url>
cd soe-investment-compliance
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run Backend

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload
```

### 3. Run Frontend

Open `frontend/index.html` in a browser, or serve it:

```bash
cd frontend
python -m http.server 3000
```

### 4. Run Tests

```bash
pytest tests/ -v --cov=backend --cov-report=term-missing
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t soe-investment-compliance .

# Run container
docker run -d \
  --name soe-compliance \
  -p 8017:8017 \
  -v soe-data:/app/data \
  soe-investment-compliance
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Production Deployment

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./soe_investment_compliance.db` | Database connection string |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8017` | Server port |
| `LOG_LEVEL` | `info` | Logging level |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name compliance.example.com;

    location / {
        proxy_pass http://127.0.0.1:8017;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/frontend/;
        expires 1d;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=SOE Investment Compliance API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/soe-investment-compliance/backend
ExecStart=/opt/soe-investment-compliance/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8017
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Health Check

```bash
curl http://localhost:8017/api/health
# Expected: {"status": "ok", "timestamp": "..."}
```

### Audit Logs

```bash
curl http://localhost:8017/api/audit_logs?limit=50
```

## Backup

The SQLite database file is at `backend/soe_investment_compliance.db`. Back it up regularly:

```bash
cp backend/soe_investment_compliance.db backups/compliance_$(date +%Y%m%d).db
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8017 in use | Change port with `--port <port>` |
| Database locked | Ensure only one process accesses the DB |
| CORS errors | Set `CORS_ORIGINS` environment variable |
| Import errors | Ensure you're in the project root directory |
