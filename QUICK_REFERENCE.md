# Quick Reference Guide

## File Structure Overview

```
Sonosano/
├── app/                          # Frontend (React/Electron)
│   ├── components/              # React components
│   ├── hooks/                   # React hooks
│   ├── pages/                   # Page components
│   ├── api/                     # API client
│   ├── providers/               # Context providers
│   └── renderer.tsx             # Main renderer
│
├── backend/                      # Python FastAPI backend
│   ├── src/
│   │   ├── main.py             # ⭐ Application entry point
│   │   ├── core/               # Core business logic
│   │   │   ├── slskd_manager.py   # ⭐ Main SlskcManager class
│   │   │   ├── library_service.py # Library DB management
│   │   │   ├── metadata_service.py
│   │   │   ├── song_processor.py
│   │   │   └── ...
│   │   ├── api/                # FastAPI route handlers
│   │   │   ├── search_routes.py    # ⭐ Search endpoints
│   │   │   ├── download_routes.py  # ⭐ Download endpoints
│   │   │   ├── system_routes.py    # ⭐ System endpoints
│   │   │   └── ...
│   │   ├── models/             # Pydantic data models
│   │   └── utils/              # Utility functions
│   ├── requirements.txt         # Python dependencies
│   └── sonosano.spec          # PyInstaller config
│
├── .env                         # Environment variables
├── BACKEND_API_REFERENCE.md    # 📖 API & class documentation
├── BUILD_RUN_COMMANDS.md       # 📖 Build/run commands
├── MIGRATION_NOTES.md          # 📖 Migration details
└── VERIFICATION_REPORT.md      # 📖 Migration verification
```

---

## Essential Class Diagram

```
SlskcManager (core/slskd_manager.py)
├── Properties:
│   ├── logged_in: bool
│   ├── search_results: dict {token → [results]}
│   ├── download_status: dict {download_id → status}
│   ├── active_downloads: dict {download_id → info}
│   └── client: SlskdClient
│
├── Public Methods:
│   ├── initialize_slskd()
│   ├── perform_search(artist, song, query) → (token, query)
│   ├── get_search_results(token) → [results]
│   ├── download_file(username, path, size) → download_id
│   ├── get_download_status(username, path) → status
│   ├── is_logged_in() → bool
│   └── wait_for_login(timeout=30) → bool
│
└── Private Methods (Background Threads):
    ├── _poll_search_results(token, search_id)
    └── _monitor_download(download_id, username, path)
```

---

## API Endpoint Map

### Search Endpoints

| Method | Endpoint                           | Purpose                         |
| ------ | ---------------------------------- | ------------------------------- |
| POST   | `/search/soulseek`                 | Start a search, returns token   |
| GET    | `/search/soulseek/results/{token}` | Get accumulated results         |
| GET    | `/search`                          | Generic search across providers |

### Download Endpoints

| Method | Endpoint                         | Purpose                           |
| ------ | -------------------------------- | --------------------------------- |
| POST   | `/download`                      | Start a download                  |
| GET    | `/download-status/{user}/{path}` | Get download progress             |
| GET    | `/downloads/status`              | Get all downloads + system status |
| POST   | `/download/cancel/{id}`          | Cancel a download                 |

### System Endpoints

| Method | Endpoint                | Purpose                     |
| ------ | ----------------------- | --------------------------- |
| GET    | `/health`               | Health check                |
| GET    | `/connection/status`    | Soulseek connection status  |
| GET    | `/download-dir`         | Get download directory path |
| GET    | `/play-file/{filename}` | Stream audio file           |
| POST   | `/show-in-explorer`     | Open file in explorer       |
| GET    | `/sharing/status`       | Sharing statistics          |
| POST   | `/sharing/rescan`       | Rescan shared folders       |

### Library Endpoints

| Method | Endpoint          | Purpose               |
| ------ | ----------------- | --------------------- |
| GET    | `/library/songs`  | Get all library songs |
| GET    | `/library/lyrics` | Get cached lyrics     |
| POST   | `/library/sync`   | Sync with file system |

### Configuration Endpoints

| Method | Endpoint    | Purpose           |
| ------ | ----------- | ----------------- |
| GET    | `/config`   | Get app config    |
| POST   | `/config`   | Update app config |
| POST   | `/romanize` | Romanize text     |

---

## Development Workflow

### Start Backend Development

```bash
cd backend/src
python -m uvicorn main:app --reload
```

- Listens on `http://localhost:8000`
- Auto-reloads on file changes
- Requires `.env` with credentials
- Requires slskd running on `http://localhost:5030`

### Start Frontend Development

```bash
npm run dev
```

- Launches Electron app
- Hot reload enabled
- Connects to backend at `http://localhost:8000`

### Check Status

```bash
curl http://localhost:8000/health
# Returns: {"status":"healthy","soulseek_connected":true}
```

---

## Data Flow Examples

### Search Flow Diagram

```
Frontend
   ↓
POST /search/soulseek {artist, song, query}
   ↓
search_routes.search_files()
   ↓
SlskcManager.perform_search()
   │
   ├─→ Generate token (int)
   ├─→ Build search term
   ├─→ Call slskd API
   └─→ Spawn background thread (_poll_search_results)
   ↓
Return {token, query}
   ↓
Frontend polls GET /search/soulseek/results/{token}
   ↓
search_routes.get_search_results()
   ↓
Return accumulated results from SlskcManager.search_results[token]
   ↓
Background thread updates results (runs up to 30 seconds)
```

### Download Flow Diagram

```
Frontend
   ↓
POST /download {username, file_path, size, metadata}
   ↓
download_routes.download_file()
   ↓
SlskcManager.download_file()
   │
   ├─→ Create download_id ("username:filepath")
   ├─→ Store metadata
   ├─→ Add to active_downloads
   ├─→ Call slskd API
   └─→ Spawn background thread (_monitor_download)
   ↓
Return {download_id}
   ↓
Frontend polls GET /download-status/{user}/{path}
   ↓
download_routes.get_download_status()
   ↓
Return status from SlskcManager.download_status[id]
   ↓
Background thread monitors and updates status (up to 5 minutes)
```

---

## Common Code Locations

### To add a new Search feature:

- Edit: `backend/src/api/search_routes.py` (add endpoint)
- Uses: `core/slskd_manager.py` (perform_search, get_search_results)
- Models: `models/search_models.py` (SearchQuery, SearchResult)

### To add a new Download feature:

- Edit: `backend/src/api/download_routes.py` (add endpoint)
- Uses: `core/slskd_manager.py` (download_file, get_download_status)
- Models: `models/download_models.py` (DownloadRequest, DownloadStatus)

### To add a new System/Config feature:

- Edit: `backend/src/api/system_routes.py` (add endpoint)
- Uses: `core/slskd_manager.py` (if Soulseek-related)
- Models: `models/system_models.py` (status models)

### To modify slskd integration:

- Edit: `backend/src/core/slskd_manager.py` (SlskcManager class)
- Related: `main.py` (initialization)
- Related: `.env` (credentials and URL)

### To add Library/Metadata features:

- Edit: `backend/src/core/library_service.py`
- Or: `backend/src/core/metadata_service.py`
- Or: `backend/src/api/library_routes.py` (endpoints)

---

## Environment Setup Quick Reference

### .env Template

```
USERNAME=your_soulseek_username
PASSWORD=your_soulseek_password
APIKEY=your_slskd_api_key
SLSKD_URL=http://localhost:5030
```

### Directory Structure

```
{Documents}/Sonosano_Songs/
├── downloads/          # Downloaded music files
├── covers/            # Album cover cache
├── temp/              # Temporary files
├── library.db         # Song database
├── config.ini         # Config file
└── misc.json          # Misc data
```

---

## Testing Checklist

- [ ] Backend starts without errors: `python -m uvicorn main:app --reload`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Migration verified: `python verify_migration.py`
- [ ] SlskcManager loads: `python -c "from core.slskd_manager import SlskcManager"`
- [ ] All imports work: `python -c "from api import search_routes, download_routes"`
- [ ] FastAPI app instantiates: `python -c "from main import app"`
- [ ] Connection status works: `curl http://localhost:8000/connection/status`
- [ ] Download dir accessible: `curl http://localhost:8000/download-dir`
- [ ] Library loads: `curl http://localhost:8000/library/songs`

---

## Documentation Links

- **Full API Reference:** See `BACKEND_API_REFERENCE.md`
  - All classes and methods
  - Endpoint documentation
  - Data models
  - Examples

- **Build & Run Commands:** See `BUILD_RUN_COMMANDS.md`
  - Development setup
  - Running backend/frontend
  - Production builds
  - Testing & verification
  - Debugging tips
  - Troubleshooting

- **Migration Details:** See `MIGRATION_NOTES.md`
  - What changed from Pynicotine
  - Architecture comparison
  - Benefits of slskd

- **Verification Report:** See `VERIFICATION_REPORT.md`
  - Migration validation results
  - File integrity checks
  - Import tests

---

## Key Points to Remember

1. **SlskcManager** is the core class - all Soulseek operations go through here
2. **Background threads** handle polling (searches up to 30s, downloads up to 5m)
3. **Tokens** are used to track searches (frontend polls with token for results)
4. **Download IDs** are `username:filepath` format
5. **All communication** uses REST API endpoints (see endpoint map above)
6. **.env file** is REQUIRED (has credentials)
7. **slskd server** must be running on `http://localhost:5030`
8. **Download directory** is `{data_path}/downloads` (auto-created)
9. **Database** is TinyDB in JSON format at `{data_path}/library.db`
10. **No more pynicotine** - all code uses slskd-api instead

---

## Quick Debugging Checklist

- [ ] Check `.env` file exists and has correct credentials
- [ ] Verify slskd server is running: `curl http://localhost:5030/`
- [ ] Check backend started: `curl http://localhost:8000/health`
- [ ] Verify connection: `curl http://localhost:8000/connection/status`
- [ ] Check logs in terminal for errors
- [ ] Run `python verify_migration.py` to check setup
- [ ] Clear Python cache: `find . -name __pycache__ -type d -exec rm -rf {} +`
- [ ] Restart backend with `--log-level debug`
- [ ] Check if port 8000 is already in use: `netstat -ano | findstr :8000`
