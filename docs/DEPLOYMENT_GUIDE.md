# Aegis Phase 1 Software - Deployment Guide

**Date:** May 24, 2026  
**Version:** 1.0 (Release)  
**Status:** Production Ready

---

## Overview

Aegis is a **multi-tiered IoT audit platform** for industrial compliance, biosphere management, and agricultural operations. This guide provides step-by-step instructions for deploying the complete Phase 1 software stack.

**System Components:**
- FastAPI Backend (async REST + gRPC integration)
- PostgreSQL Database (with SQLAlchemy ORM + Alembic migrations)
- Next.js Frontend (TypeScript + Tailwind CSS)
- Solidity Smart Contracts (blockchain audit trail)
- Vryndara gRPC Kernel (orchestration + AI)

**Deployment Target Environments:**
- Development (local, SQLite, mocked services)
- Staging (Docker, PostgreSQL, integrated systems)
- Production (Kubernetes, PostgreSQL HA, full monitoring)

---

## Pre-Deployment Checklist

### System Requirements

#### Development / Staging
- **OS:** Linux (Ubuntu 20.04+), macOS 12+, or Windows 10+ (WSL2)
- **Python:** 3.10.20 (required for web3/eth_abi compatibility)
- **Node.js:** 18.0.0+
- **PostgreSQL:** 13.0+ (staging/production)
- **Docker:** 20.10+ (recommended for containerization)

#### Production
- **Kubernetes:** 1.24+ (Helm 3.0+)
- **PostgreSQL:** 14.0+ with HA setup
- **Redis:** 7.0+ (caching + session store)
- **gRPC Server:** Vryndara kernel (localhost:50051)

### Pre-Flight Checks
```bash
# Verify Python version
python --version  # Should be 3.10.20

# Verify Node.js version
node --version  # Should be 18.0.0+

# Verify PostgreSQL connectivity (for staging/production)
psql -h localhost -U postgres -d postgres -c "SELECT version();"

# Verify Docker (if using containers)
docker --version
docker-compose --version
```

---

## Installation Steps

### Step 1: Clone Repository & Environment Setup

```bash
# Clone the Aegis repository
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt
pip install -r tests/requirements.txt  # For testing

# Verify installation
python -c "import fastapi, sqlalchemy, web3; print('✅ Core dependencies installed')"
```

### Step 2: Database Setup

#### Development (SQLite)
```bash
# No additional setup needed - SQLite creates database automatically
# Test database will be created as ./test.db during testing
```

#### Staging / Production (PostgreSQL)
```bash
# Create database
createdb aegis_db
createuser aegis_user -P  # Set password when prompted

# Grant privileges
psql -U postgres << EOF
GRANT ALL PRIVILEGES ON DATABASE aegis_db TO aegis_user;
ALTER ROLE aegis_user CREATEDB;
EOF

# Set environment variables
export DATABASE_URL="postgresql://aegis_user:password@localhost:5432/aegis_db"
export SQLALCHEMY_ECHO="false"  # Disable SQL query logging in production

# Run database migrations
cd backend
alembic upgrade head
cd ..
```

### Step 3: Environment Configuration

```bash
# Create .env file in project root
cat > .env << 'EOF'
# Backend Configuration
ENVIRONMENT=production
DEBUG=false
SERVER_HOST=0.0.0.0
SERVER_PORT=8001

# Database
DATABASE_URL=postgresql://aegis_user:password@localhost:5432/aegis_db
SQLALCHEMY_ECHO=false

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://aegis.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# Vryndara Integration
VRYNDARA_HOST=localhost
VRYNDARA_PORT=50051
VRYNDARA_TIMEOUT=5
VRYNDARA_FALLBACK_ENABLED=true

# Blockchain
BLOCKCHAIN_NETWORK=http://127.0.0.1:8545
BLOCKCHAIN_CONTRACT_ADDRESS=0x...  # Deploy and set after contract deployment
BLOCKCHAIN_PRIVATE_KEY=your-private-key  # Secure storage recommended

# Email (for password resets)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

# Source environment
export $(cat .env | xargs)
```

### Step 4: Backend Deployment

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run database migrations
cd backend
alembic upgrade head

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# In production, use:
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete
```

### Step 5: Frontend Deployment

```bash
# Install Node.js dependencies
cd frontend
npm install

# Build for production
npm run build

# Start frontend (development)
npm run dev  # Runs on http://localhost:3000

# Start frontend (production)
npm start    # Requires `next export` first
```

### Step 6: Blockchain Deployment

```bash
# Install Hardhat dependencies
cd blockchain
npm install

# Compile smart contracts
npx hardhat compile

# Deploy to local network
npx hardhat run scripts/deploy.js --network localhost

# Deploy to testnet (e.g., Sepolia)
npx hardhat run scripts/deploy.js --network sepolia

# Update CONTRACT_ADDRESS in .env with deployed contract
```

### Step 7: Verify Deployment

```bash
# Test health check
curl http://localhost:8001/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "dependencies": {
#     "database": "connected",
#     "blockchain": "connected",
#     "vryndara": "connected"
#   }
# }

# Test authentication endpoint
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aegis.local","password":"admin123"}'

# Test sensor endpoint
curl http://localhost:8001/api/v1/sensors \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Docker Deployment

### Option 1: Docker Compose (All-in-One)

```bash
# Create docker-compose.yml in project root
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: aegis_db
      POSTGRES_USER: aegis_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8001:8001"
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://aegis_user:secure_password@postgres:5432/aegis_db
      VRYNDARA_HOST: vryndara-kernel
    networks:
      - aegis-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    networks:
      - aegis-network

volumes:
  postgres_data:

networks:
  aegis-network:
    driver: bridge
EOF

# Start containers
docker-compose up -d

# Verify containers running
docker-compose ps
```

### Option 2: Kubernetes Deployment

```bash
# Create Kubernetes manifests directory
mkdir -p k8s

# Create deployment manifest
cat > k8s/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aegis-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aegis-backend
  template:
    metadata:
      labels:
        app: aegis-backend
    spec:
      containers:
      - name: backend
        image: aegis-backend:1.0
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aegis-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: aegis-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
EOF

# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
```

---

## Configuration Management

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` | Deployment environment (dev, staging, prod) |
| `DEBUG` | `true` | Enable debug logging |
| `SERVER_HOST` | `127.0.0.1` | Server bind address |
| `SERVER_PORT` | `8001` | Server port |
| `DATABASE_URL` | `sqlite:///./aegis.db` | Database connection string |
| `JWT_SECRET_KEY` | *(required)* | JWT signing secret |
| `VRYNDARA_HOST` | `localhost` | Vryndara kernel host |
| `VRYNDARA_PORT` | `50051` | Vryndara kernel port |
| `BLOCKCHAIN_NETWORK` | `http://127.0.0.1:8545` | Blockchain RPC endpoint |

### Secrets Management (Production)

```bash
# Using HashiCorp Vault
vault kv put secret/aegis/prod \
  database_url="postgresql://..." \
  jwt_secret="..." \
  blockchain_private_key="..."

# Using AWS Secrets Manager
aws secretsmanager create-secret \
  --name aegis/prod/secrets \
  --secret-string '{"database_url":"...","jwt_secret":"..."}'

# Using Kubernetes Secrets
kubectl create secret generic aegis-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=jwt-secret="..."
```

---

## Post-Deployment Validation

### Automated Test Suite (30 tests)

```bash
# Run complete test suite
pytest tests/test_day59_*.py -v

# Expected output:
# ============================== 30 passed in X.XXs ==============================
# ✅ E2E Integration: 5/5 PASSED
# ✅ Performance: 11/11 PASSED
# ✅ Security: 14/14 PASSED
```

### Manual Testing

```bash
# 1. Test API endpoints
curl http://localhost:8001/api/v1/health

# 2. Test authentication
JWT=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aegis.local","password":"admin123"}' \
  | jq -r '.access_token')

# 3. Test protected endpoint
curl http://localhost:8001/api/v1/sensors \
  -H "Authorization: Bearer $JWT"

# 4. Test frontend
open http://localhost:3000

# 5. Test blockchain
curl http://localhost:8001/api/v1/audit \
  -H "Authorization: Bearer $JWT"
```

---

## Monitoring & Observability

### Logging Configuration

```python
# backend/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger("aegis")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Metrics Collection

```bash
# Install Prometheus client
pip install prometheus-client

# Access metrics endpoint
curl http://localhost:8001/metrics
```

### Health Checks

```bash
# Liveness probe
curl http://localhost:8001/health

# Readiness probe
curl http://localhost:8001/ready

# Deep dependency check
curl http://localhost:8001/api/v1/health
```

---

## Rollback Procedures

### Database Rollback

```bash
# If migration fails, rollback to previous version
cd backend
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations

# Verify rollback
alembic current
```

### Container Rollback (Kubernetes)

```bash
# Check rollout history
kubectl rollout history deployment/aegis-backend

# Rollback to previous deployment
kubectl rollout undo deployment/aegis-backend

# Rollback to specific revision
kubectl rollout undo deployment/aegis-backend --to-revision=1
```

---

## Troubleshooting

### Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Database connection failed | `sqlalchemy.exc.OperationalError` | Verify DATABASE_URL, check PostgreSQL running |
| JWT validation failed | `401 Unauthorized` | Check JWT_SECRET_KEY matches, verify token format |
| Blockchain not responding | Health check shows `blockchain: disconnected` | Ensure Ethereum node is running on port 8545 |
| Vryndara kernel timeout | `TimeoutError in gRPC call` | Check VRYNDARA_HOST and VRYNDARA_PORT, verify kernel is running |
| CORS errors in frontend | Browser shows CORS error | Update CORS_ORIGINS in .env, restart backend |
| Out of memory | Container exits with OOM error | Increase memory limits in Docker/Kubernetes |

### Logs

```bash
# Backend logs
docker logs aegis_backend

# Frontend logs
npm logs  # Check console output

# Database logs
docker logs aegis_postgres
```

---

## Maintenance

### Regular Tasks

- **Daily:** Monitor health check endpoint, review error logs
- **Weekly:** Review performance metrics, check for security updates
- **Monthly:** Database backup, dependency updates, security audit

### Updates & Patches

```bash
# Update Python dependencies
pip install --upgrade -r backend/requirements.txt

# Update Node.js dependencies
npm update

# Check for security vulnerabilities
pip audit
npm audit

# Update database schema
alembic upgrade head
```

---

## Support & Documentation

- **API Documentation:** http://localhost:8001/docs (Swagger UI)
- **Component Documentation:** See [DEVELOPER_GUIDE.md](guides/DEVELOPER_GUIDE.md)
- **System Architecture:** See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- **Integration Guide:** See [VRYNDARA_INTEGRATION_GUIDE.md](VRYNDARA_INTEGRATION_GUIDE.md)

---

**Deployment Status:** ✅ Ready for Production  
**Last Updated:** May 24, 2026  
**Next Phase:** Phase 2 Hardware Development (Days 71-150)
