# Aegis Installation Guide - Operating System Specific

**Target Platforms:** Linux, macOS, Windows (WSL2)  
**Installation Time:** ~20-30 minutes  
**Required Skills:** Basic command line, basic understanding of databases

---

## Quick Start (All Platforms)

```bash
# 1. Clone repository
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# 2. Create Python environment
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Start backend
cd backend && uvicorn main:app --reload

# 6. In another terminal, start frontend
cd frontend && npm install && npm run dev

# 7. Access the application
# Backend API: http://localhost:8001
# Frontend: http://localhost:3000
# API Docs: http://localhost:8001/docs
```

---

## Platform-Specific Instructions

### Linux (Ubuntu 20.04 / 22.04)

#### Prerequisites
```bash
# Update package manager
sudo apt-get update

# Install Python 3.10
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev

# Install Node.js 18
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PostgreSQL (optional, for production)
sudo apt-get install -y postgresql postgresql-contrib

# Install Git
sudo apt-get install -y git
```

#### Installation Steps
```bash
# 1. Clone and setup
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt

# 4. Configure database (development)
# SQLite is default, no additional setup needed
# For PostgreSQL:
sudo -u postgres createdb aegis_db
sudo -u postgres createuser aegis_user -P

# 5. Run migrations
cd backend && alembic upgrade head && cd ..

# 6. Start services (in separate terminals)
# Terminal 1: Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && npm install && npm run dev

# Terminal 3: AI service (optional)
cd ai && python orchestrator.py
```

#### Verify Installation
```bash
# Check Python version
python --version  # Should show 3.10.20

# Check Node.js version
node --version  # Should show 18.x

# Test backend
curl http://localhost:8001/api/v1/health

# Test frontend
curl http://localhost:3000

# Run tests
cd .. && pytest tests/test_day59_*.py -v
```

---

### macOS (12+)

#### Prerequisites
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.10
brew install python@3.10

# Install Node.js 18
brew install node@18
brew link node@18 --force

# Install PostgreSQL (optional)
brew install postgresql

# Install Git (usually pre-installed)
brew install git
```

#### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt

# 4. Start PostgreSQL (if using)
brew services start postgresql

# 5. Create database
createdb aegis_db
createuser aegis_user -P

# 6. Run migrations
cd backend && alembic upgrade head && cd ..

# 7. Start services (in separate terminals)
# Terminal 1: Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && npm install && npm run dev

# Terminal 3: AI service (optional)
cd ai && python orchestrator.py
```

#### Verify Installation
```bash
# Check Python version
python3.10 --version

# Check Node.js version
node --version

# Test backend
curl http://localhost:8001/api/v1/health

# Test frontend
open http://localhost:3000

# Run tests
pytest tests/test_day59_*.py -v
```

#### Troubleshooting (macOS)
```bash
# If Python not found, add to PATH
export PATH="/usr/local/opt/python@3.10/bin:$PATH"

# If Node.js not linked properly
brew link node@18 --force --overwrite

# If PostgreSQL connection fails
brew services restart postgresql
```

---

### Windows 10+ (WSL2)

#### Prerequisites
```powershell
# 1. Enable WSL2
wsl --install

# 2. Install Linux distribution
wsl --install -d Ubuntu-22.04

# 3. Open WSL2 terminal
wsl

# Inside WSL2 terminal:
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev

# Install Node.js
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Git
sudo apt-get install -y git
```

#### Installation Steps (WSL2)
```bash
# 1. Clone repository (inside WSL2)
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt

# 4. Configure database (SQLite is default)
cd backend && alembic upgrade head && cd ..

# 5. Start backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 6. In another WSL2 terminal, start frontend
cd aegis/frontend && npm install && npm run dev

# 7. Access from Windows host
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
```

#### Verify Installation (WSL2)
```bash
# Check Python
python --version

# Check Node.js
node --version

# Test from Windows PowerShell (not WSL2)
curl http://localhost:8001/api/v1/health
Invoke-WebRequest http://localhost:3000
```

#### Troubleshooting (Windows/WSL2)
```bash
# If port 8001 already in use
netstat -ano | findstr :8001  # Find PID
taskkill /PID <PID> /F

# If WSL2 not accessible from Windows
# Check firewall settings and ensure WSL2 networking enabled

# If npm modules not installing
npm install --legacy-peer-deps

# If venv activation fails
source venv/Scripts/activate  # Correct for WSL2
```

---

## Docker Installation (All Platforms)

### Prerequisites
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
docker --version  # Verify installation
docker-compose --version
```

### Docker Compose Setup
```bash
# 1. Clone repository
git clone https://github.com/aegis-biosphere/aegis.git
cd aegis

# 2. Create docker-compose.yml (already in repository)
cat docker-compose.yml

# 3. Start all services
docker-compose up -d

# 4. Verify services
docker-compose ps

# 5. View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# 6. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
# API Docs: http://localhost:8001/docs

# 7. Stop services
docker-compose down
```

### Build Custom Docker Image
```bash
# Build backend image
docker build -f Dockerfile.backend -t aegis-backend:1.0 .

# Build frontend image
docker build -f frontend/Dockerfile -t aegis-frontend:1.0 ./frontend

# Run containers
docker run -d -p 8001:8001 aegis-backend:1.0
docker run -d -p 3000:3000 aegis-frontend:1.0
```

---

## Dependency Management

### Python Dependencies

**Core Dependencies:**
```
fastapi>=0.100.0
uvicorn>=0.23.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-jose>=3.3.0
python-multipart>=0.0.6
pydantic-settings>=2.0.0
```

**Data Science Dependencies:**
```
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
tensorflow>=2.13.0
torch>=2.0.0
```

**Blockchain Dependencies:**
```
web3>=6.0.0
eth-account>=0.9.0
eth-abi>=4.0.0
```

### Node.js Dependencies

**Core Dependencies:**
```
next>=14.0.0
react>=18.0.0
react-dom>=18.0.0
tailwindcss>=3.0.0
typescript>=5.0.0
```

**Testing Dependencies:**
```
jest>=29.0.0
@testing-library/react>=14.0.0
cypress>=13.0.0
```

---

## Database Setup

### SQLite (Development)
```bash
# No installation needed - automatically created on first run
# Database location: ./test.db

# To reset database
rm test.db
alembic upgrade head
```

### PostgreSQL (Production)
```bash
# Create database and user
createdb aegis_db
createuser aegis_user -P

# Grant privileges
psql << EOF
GRANT ALL PRIVILEGES ON DATABASE aegis_db TO aegis_user;
ALTER ROLE aegis_user CREATEDB;
EOF

# Run migrations
alembic upgrade head

# Verify connection
psql -U aegis_user -d aegis_db -c "SELECT version();"
```

---

## Environment Configuration

Create `.env` file in project root:

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8001

# Database
DATABASE_URL=sqlite:///./aegis.db
# For PostgreSQL:
# DATABASE_URL=postgresql://aegis_user:password@localhost:5432/aegis_db

# JWT
JWT_SECRET_KEY=your-dev-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Vryndara
VRYNDARA_HOST=localhost
VRYNDARA_PORT=50051

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Verification Checklist

- [ ] Python 3.10 installed
- [ ] Node.js 18+ installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] Python dependencies installed
- [ ] Node dependencies installed
- [ ] Database migrations run
- [ ] .env file configured
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Health check endpoint responding
- [ ] Tests passing (30/30)
- [ ] API documentation accessible
- [ ] Frontend accessible in browser

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r backend/requirements.txt` |
| `Python version mismatch` | Verify Python 3.10: `python --version` |
| `Port 8001 already in use` | Kill process using port or use different port |
| `Database connection failed` | Check DATABASE_URL, verify PostgreSQL running |
| `npm ERR! ERESOLVE could not resolve dependencies` | Run `npm install --legacy-peer-deps` |
| `CORS errors in browser console` | Verify CORS_ORIGINS in .env matches frontend URL |
| `venv activation fails` | Use correct activation command for your OS |

---

## Next Steps

1. ✅ Installation complete
2. Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development workflow
3. Review [API documentation](http://localhost:8001/docs)
4. Run test suite: `pytest tests/test_day59_*.py -v`
5. Deploy to production using [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Installation Guide Version:** 1.0  
**Last Updated:** May 24, 2026  
**Support:** See README.md for community support channels
