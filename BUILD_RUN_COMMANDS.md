# Sonosano - Build & Run Commands

## Table of Contents
1. [Development Setup](#development-setup)
2. [Running the Backend](#running-the-backend)
3. [Running the Frontend](#running-the-frontend)
4. [Building for Production](#building-for-production)
5. [Testing & Verification](#testing--verification)
6. [Debugging](#debugging)
7. [Database & Configuration](#database--configuration)
8. [Dependencies Management](#dependencies-management)

---

## Development Setup

### Initial Setup (First Time)

```bash
# Clone the repository
git clone <repository-url>
cd Sonosano

# Setup Backend Virtual Environment
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Install slskd-api and python-dotenv (if not in requirements.txt)
pip install slskd-api python-dotenv

# Go to project root
cd ..

# Setup Frontend
npm install
```

### Install Additional Python Packages

```bash
# From backend directory
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt
```

---

## Running the Backend

### Development Mode (with auto-reload)

```bash
# From backend/src directory
cd backend/src

# Start with uvicorn auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with logging
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Production Mode

```bash
# From backend/src directory
cd backend/src

# Start without auto-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With production logging
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning
```

### Run with Custom Configuration

```bash
# Set environment variables before running
set SLSKD_URL=http://slskd-server:5030
set USERNAME=your_username
set PASSWORD=your_password
set APIKEY=your_api_key

# Then start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Check Backend Health

```bash
# From any directory, test the health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","soulseek_connected":true}
```

---

## Running the Frontend

### Development Mode

```bash
# From project root
npm run dev

# This starts Electron in development mode
# with hot reload
```

### Production Build

```bash
# From project root
npm run build

# Create Electron build for current platform
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

### Development Mode with DevTools

```bash
npm run dev

# Press F12 to open DevTools
# Ctrl+Shift+R to reload
```

---

## Building for Production

### Complete Production Build

```bash
# From project root
# 1. Build backend executable
npm run build:backend

# 2. Build Electron app
npm run build

# 3. Output will be in dist/ or build/ directory
```

### Backend Production Build

```bash
cd backend

# Using PyInstaller (configured in sonosano.spec)
pyinstaller sonosano.spec

# Output: backend/dist/sonosano.exe (Windows) or sonosano (Unix)
```

### Build Backend Only

```bash
cd backend

# Using the build script
node scripts/build-backend.js

# Or directly with PyInstaller
python -m PyInstaller sonosano.spec
```

### Build Frontend Only

```bash
# From project root
npm run build

# Output: dist/Sonosano-x.x.x.exe (Windows)
#         dist/Sonosano-x.x.x.dmg (macOS)
#         dist/Sonosano-x.x.x.AppImage (Linux)
```

---

## Testing & Verification

### Verify Migration

```bash
# From backend/src directory
python verify_migration.py

# Output shows:
# - File integrity ✓
# - Python syntax ✓
# - Import validation ✓
# - Pynicotine cleanup ✓
# - SlskcManager integration ✓
# - FastAPI app instantiation ✓
```

### Test Backend Startup

```bash
# From backend/src directory
python -c "from main import app; print('✓ App loaded successfully')"
```

### Test Imports

```bash
# From backend/src directory
python -c "
from core.slskd_manager import SlskcManager
from api import search_routes, download_routes, system_routes
print('✓ All imports successful')
"
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get connection status
curl http://localhost:8000/connection/status

# Get download directory
curl http://localhost:8000/download-dir

# Get all library songs
curl http://localhost:8000/library/songs

# Search Soulseek (requires auth)
curl -X POST http://localhost:8000/search/soulseek \
  -H "Content-Type: application/json" \
  -d '{"artist":"The Beatles","song":"Let It Be","query":"The Beatles Let It Be"}'
```

### Check Database

```bash
# Verify library database is initialized
# Database location: {data_path}/library.db

# From backend/src, test library access
python -c "
from core.library_service import LibraryService
from core.metadata_service import MetadataService
lib = LibraryService(MetadataService('.'), '.')
songs = lib.get_all_songs()
print(f'✓ Library contains {len(songs)} songs')
"
```

---

## Debugging

### Enable Debug Logging

```bash
# From backend/src
PYTHONUNBUFFERED=1 python -m uvicorn main:app --reload --log-level debug
```

### Debug with Python Debugger

```bash
# Add breakpoint in code
# backend/src/core/slskd_manager.py

def perform_search(self, artist, song, raw_query):
    import pdb; pdb.set_trace()  # Debugger will stop here
    # ... rest of code
```

### Then run:
```bash
cd backend/src
python main.py
```

### Debug with VSCode

1. Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--log-level", "debug"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend/src",
      "console": "integratedTerminal"
    }
  ]
}
```

2. Press F5 to start debugging

### Check logs

```bash
# Backend logs are printed to console
# Look for entries from:
# - SlskcManager.__init__ → Initialization logs
# - SlskcManager.initialize_slskd → Login logs
# - SlskcManager.perform_search → Search logs
# - SlskcManager.download_file → Download logs

# Check file watcher logs
# Watch for entries about new/deleted songs
```

---

## Database & Configuration

### Reset Library Database

```bash
# Find database location from config
# Usually: {Documents}/Sonosano_Songs/library.db

# Delete the database file
rm {path-to-library.db}

# Application will recreate empty database on next start
```

### View Configuration

```bash
# Config location: {Documents}/Sonosano_Songs/config.ini

# Example content:
# [Paths]
# dataPath = /Users/username/Documents/Sonosano_Songs
```

### Update Configuration

```bash
# Via API
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"dataPath":"/new/path/to/data"}'

# Or directly edit config.ini file
```

### .env Configuration

```bash
# Create/edit .env in project root
cat > .env << EOF
USERNAME=your_soulseek_username
PASSWORD=your_soulseek_password
APIKEY=your_slskd_api_key
SLSKD_URL=http://localhost:5030
EOF
```

### View .env

```bash
# From project root
cat .env

# Or on Windows
type .env
```

---

## Dependencies Management

### View Installed Packages

```bash
# From backend directory with venv activated
pip list

# Or check specific package
pip show slskd-api
```

### Update All Dependencies

```bash
# From backend directory
pip install --upgrade pip
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt
```

### Add New Backend Dependency

```bash
# Install package
pip install <package-name>

# Add to requirements.txt
pip freeze | grep <package-name> >> requirements.txt
```

### Remove Unused Dependencies

```bash
# Find unused imports
pip install vulture

# Check code for unused imports
vulture backend/src/

# Remove from requirements.txt manually
# Then uninstall
pip uninstall <package-name>
```

### Update NPM Packages (Frontend)

```bash
# Check for updates
npm outdated

# Update all
npm update

# Or update specific package
npm install <package-name>@latest
```

---

## Common Commands Cheatsheet

### Quick Start (Development)

```bash
# Terminal 1: Backend
cd backend/src
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd Sonosano
npm run dev
```

### Quick Verify

```bash
# Check migration status
cd backend/src
python verify_migration.py

# Test connection
curl http://localhost:8000/health
```

### Quick Clean

```bash
# Remove all Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remove node_modules (if needed)
rm -rf node_modules
npm install
```

### Full Rebuild

```bash
# Backend
cd backend
rm -rf venv
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ..
rm -rf node_modules
npm install
npm run build
```

---

## Environment Variables Reference

### Backend (.env file)

| Variable | Description | Example |
|----------|-------------|---------|
| `USERNAME` | Soulseek username | `sonosano_user` |
| `PASSWORD` | Soulseek password | `mypassword123` |
| `APIKEY` | slskd API key | `abc123def456...` |
| `SLSKD_URL` | slskd server URL | `http://localhost:5030` |

### Application Paths

| Path | Purpose |
|------|---------|
| `{Documents}/Sonosano_Songs/` | Root data directory |
| `{Documents}/Sonosano_Songs/downloads/` | Downloaded music files |
| `{Documents}/Sonosano_Songs/covers/` | Album cover cache |
| `{Documents}/Sonosano_Songs/library.db` | Song metadata database |
| `{Documents}/Sonosano_Songs/config.ini` | Application configuration |

---

## Troubleshooting Commands

### Backend Won't Start

```bash
# 1. Check Python version
python --version  # Should be 3.8+

# 2. Check venv is activated
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate

# 3. Check dependencies installed
pip list | grep -E "fastapi|uvicorn|slskd-api"

# 4. Verify syntax
python -m py_compile backend/src/main.py
```

### Can't Connect to Soulseek

```bash
# 1. Check slskd is running
curl http://localhost:5030/

# 2. Verify credentials in .env
cat .env

# 3. Check SlskcManager initialization
cd backend/src
python -c "from core.slskd_manager import SlskcManager; print('✓ SlskcManager loads')"
```

### Port Already in Use

```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# macOS/Linux:
lsof -i :8000

# Kill the process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>           # macOS/Linux

# Or use different port
python -m uvicorn main:app --port 8001
```

### Clear Cache & Restart Fresh

```bash
# Backend cache
cd backend/src
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart
python -m uvicorn main:app --reload
```
