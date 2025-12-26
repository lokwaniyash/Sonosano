# Sonosano Backend - Class & Method Reference

## Table of Contents

1. [SlskcManager](#slskcmanager)
2. [Search Routes](#search-routes)
3. [Download Routes](#download-routes)
4. [System Routes](#system-routes)
5. [Library Service](#library-service)
6. [Data Models](#data-models)

---

## SlskcManager

**Location:** `backend/src/core/slskd_manager.py`

**Purpose:** Core manager class that handles all Soulseek network operations via slskd API.

### Constructor

```python
__init__(self, library_service, data_path: str)
```

- **Parameters:**
  - `library_service`: LibraryService instance for metadata management
  - `data_path`: Root data directory path
- **Initializes:**
  - Reads credentials from `.env` (USERNAME, PASSWORD, APIKEY, SLSKD_URL)
  - Creates SlskdClient connection
  - Sets up empty dictionaries for search results and download tracking

### Public Methods

#### `initialize_slskd()`

- **Purpose:** Initialize and authenticate with slskd server
- **Returns:** None
- **Side Effects:** Sets `logged_in` flag, triggers login event
- **Called From:** `main.py` startup
- **Exception Handling:** Logs errors but doesn't raise

#### `perform_search(artist: Optional[str], song: Optional[str], raw_query: str) -> tuple[int, str]`

- **Purpose:** Initiate a search on the Soulseek network
- **Parameters:**
  - `artist`: Artist name (optional)
  - `song`: Song name (optional)
  - `raw_query`: Fallback query string
- **Returns:** Tuple of (search_token, search_term)
- **Flow:**
  1. Generates unique search token
  2. Combines artist + song if available
  3. Calls slskd API to perform search
  4. Spawns background thread to poll results
- **Use Case:** Called from `/search/soulseek` endpoint

#### `get_search_results(token: int) -> List[Dict[str, Any]]`

- **Purpose:** Retrieve accumulated search results for a token
- **Parameters:**
  - `token`: Search token returned by `perform_search()`
- **Returns:** List of file result dictionaries
- **Use Case:** Called from `/search/soulseek/results/{token}` endpoint

#### `download_file(username: str, file_path: str, size: int, metadata: Optional[Dict] = None) -> str`

- **Purpose:** Initiate a file download from a user
- **Parameters:**
  - `username`: Username of file owner
  - `file_path`: Path/name of file on remote user's system
  - `size`: File size in bytes
  - `metadata`: Optional metadata dict with song info
- **Returns:** Download ID (format: "username:filepath")
- **Flow:**
  1. Creates download tracking entry
  2. Stores metadata if provided
  3. Initiates download via slskd API
  4. Starts background monitoring thread
- **Use Case:** Called from `/download` endpoint

#### `get_download_status(username: str, file_path: str) -> Dict[str, Any]`

- **Purpose:** Get current progress of a download
- **Parameters:**
  - `username`: Username of file owner
  - `file_path`: File path
- **Returns:** Status dictionary with keys:
  - `status`: 'Queued', 'Downloading', 'Finished', 'Failed', 'Cancelled'
  - `progress`: Bytes downloaded so far
  - `total`: Total file size
  - `percent`: Percentage complete (0-100)
  - `speed`: Download speed in bytes/sec
  - `queuePosition`: Position in queue (if queued)
- **Use Case:** Called from `/download-status/{username}/{file_path}` endpoint

#### `is_logged_in() -> bool`

- **Purpose:** Check if currently connected to Soulseek
- **Returns:** Boolean indicating logged-in status
- **Use Case:** Called by route handlers to validate connection

#### `wait_for_login(timeout: int = 30) -> bool`

- **Purpose:** Block until login completes or timeout
- **Parameters:**
  - `timeout`: Seconds to wait (default: 30)
- **Returns:** True if logged in, False if timeout
- **Use Case:** Called during initial library sync

### Private Methods

#### `_initialize_client()`

- **Purpose:** Create SlskdClient connection
- **Logs errors** but doesn't raise exceptions
- **Called From:** Constructor and `initialize_slskd()`

#### `_login_to_slskd()`

- **Purpose:** Authenticate with slskd server
- **Flow:**
  1. Checks server status
  2. If disconnected, initiates connection
  3. Polls for "Connected" state (30 second timeout)
  4. Sets `logged_in = True`
- **Raises:** Exception if connection times out

#### `setup_slskd_config()`

- **Purpose:** Configure slskd settings (download directory, etc.)
- **Creates:** Downloads folder at `{data_path}/downloads` if missing
- **Catches exceptions** but logs warnings instead of raising

#### `_poll_search_results(token: int, search_id: Optional[str])`

- **Purpose:** Background thread that polls for search results
- **Parameters:**
  - `token`: Search token
  - `search_id`: Search ID from slskd API
- **Flow:**
  1. Runs in daemon thread
  2. Polls for up to 30 seconds
  3. Formats results (extracts filename, size, username, bitrate, quality, length)
  4. Updates `search_results[token]`
- **Called From:** `perform_search()`

#### `_monitor_download(download_id: str, username: str, file_path: str)`

- **Purpose:** Background thread monitoring download progress
- **Flow:**
  1. Runs in daemon thread
  2. Monitors for up to 5 minutes
  3. Fetches transfer status from slskd
  4. Updates `download_status[download_id]`
  5. Stops when transfer completes/fails/cancels
- **Called From:** `download_file()`

#### `_extract_extension(path: str) -> str`

- **Purpose:** Extract file extension from path
- **Parameters:**
  - `path`: File path string
- **Returns:** Extension (e.g., '.mp3') or empty string
- **Example:** "song.mp3" → ".mp3"

### Data Structures

#### `search_results: defaultdict(list)`

- **Key:** Search token (int)
- **Value:** List of file dictionaries
- **File Dictionary Keys:** 'path', 'size', 'extension', 'username', 'bitrate', 'quality', 'length'

#### `download_status: dict`

- **Key:** Download ID (str) - format: "username:filepath"
- **Value:** Status dictionary (see `get_download_status()` returns)

#### `active_downloads: dict`

- **Key:** Download ID (str)
- **Value:** Download info dictionary with keys:
  - 'id', 'file_name', 'file_path', 'username', 'size', 'metadata', 'timestamp'

#### `search_tokens: dict`

- **Key:** Search token (int)
- **Value:** Search query string (artist + song or raw query)

---

## Search Routes

**Location:** `backend/src/api/search_routes.py`

**Purpose:** FastAPI endpoints for searching Soulseek network

### Endpoints

#### `GET /search`

- **Purpose:** Generic search across multiple providers
- **Query Parameters:**
  - `provider` (str): Which provider to search ('musicbrainz', 'spotify', etc.)
  - `q` (str): Search query
- **Returns:** JSON results from search service
- **Status Codes:**
  - 200: Success
  - 400: Missing query parameter
  - 500: Provider error

#### `POST /search/soulseek`

- **Purpose:** Search Soulseek network for audio files
- **Request Body:** SearchQuery model
  ```json
  {
    "artist": "The Beatles",
    "song": "Let It Be",
    "query": "The Beatles Let It Be"
  }
  ```
- **Returns:**
  ```json
  {
    "search_token": 1,
    "actual_query": "The Beatles Let It Be"
  }
  ```
- **Status Codes:**
  - 200: Search initiated
  - 503: Not connected to Soulseek
  - 500: Search error
- **Flow:**
  1. Validates connection to Soulseek
  2. Calls `slskd_manager.perform_search()`
  3. Returns token for polling results

#### `GET /search/soulseek/results/{token}`

- **Purpose:** Fetch accumulated search results
- **Path Parameters:**
  - `token` (int): Token from previous search
- **Returns:**
  ```json
  {
    "results": [
      {
        "path": "The Beatles/Let It Be/01-Let It Be.mp3",
        "size": 3145728,
        "username": "user123",
        "extension": ".mp3",
        "bitrate": 320,
        "quality": "320kbps",
        "length": "03:31"
      }
    ],
    "is_complete": false,
    "result_count": 5,
    "actual_query": "The Beatles Let It Be"
  }
  ```
- **Completion Logic:**
  - Complete if: 5+ consecutive polls with same count, OR 100+ results, OR token no longer tracked
  - Allows frontend to know when search is done

---

## Download Routes

**Location:** `backend/src/api/download_routes.py`

**Purpose:** FastAPI endpoints for downloading files and tracking progress

### Endpoints

#### `POST /download`

- **Purpose:** Initiate a file download
- **Request Body:** DownloadRequest model
  ```json
  {
    "username": "user123",
    "file_path": "The Beatles/Let It Be/01-Let It Be.mp3",
    "size": 3145728,
    "metadata": {
      "title": "Let It Be",
      "artist": "The Beatles",
      "album": "Let It Be"
    }
  }
  ```
- **Returns:**
  ```json
  {
    "message": "Download started",
    "download_id": "user123:The Beatles/Let It Be/01-Let It Be.mp3"
  }
  ```
- **Status Codes:**
  - 200: Download queued
  - 503: Not connected
  - 500: Download failed
- **Flow:**
  1. Validates connection
  2. Calls `slskd_manager.download_file()`
  3. Returns download ID for status polling

#### `GET /download-status/{username}/{file_path}`

- **Purpose:** Get status of a specific download
- **Path Parameters:**
  - `username` (str): Username of file owner
  - `file_path` (str): File path (URL-encoded)
- **Returns:** DownloadStatus model
  ```json
  {
    "status": "Downloading",
    "progress": 1572864,
    "total": 3145728,
    "percent": 50.0,
    "speed": 1048576,
    "queuePosition": null,
    "errorMessage": null
  }
  ```
- **Statuses:** 'Queued', 'Downloading', 'Finished', 'Failed', 'Cancelled'

#### `GET /downloads/status`

- **Purpose:** Get status of all active downloads + system status
- **Returns:** DownloadsAndStatusResponse model
  ```json
  {
    "downloads": [
      {
        "id": "user123:song1.mp3",
        "file_name": "song1.mp3",
        "file_path": "user123:song1.mp3",
        "username": "user123",
        "size": 3145728,
        "status": "Downloading",
        "progress": 1572864,
        "percent": 50.0,
        "speed": 1048576,
        "time_remaining": 2.5
      }
    ],
    "system_status": {
      "backend_status": "Online",
      "soulseek_status": "Connected",
      "soulseek_username": "sonosano_user",
      "active_uploads": 0,
      "active_downloads": 1
    }
  }
  ```

#### `POST /download/cancel/{download_id}`

- **Purpose:** Cancel an active download
- **Path Parameters:**
  - `download_id` (str): Download ID (URL-encoded)
- **Returns:**
  ```json
  {
    "message": "Download cancelled",
    "download_id": "user123:song.mp3"
  }
  ```
- **Flow:**
  1. Removes from active downloads
  2. Attempts to cancel via slskd API
  3. Clears download status tracking

---

## System Routes

**Location:** `backend/src/api/system_routes.py`

**Purpose:** System health, configuration, and utility endpoints

### Endpoints

#### `GET /`

- **Purpose:** Root endpoint
- **Returns:** `{"message": "Sonosano API is running"}`

#### `GET /health`

- **Purpose:** Health check
- **Returns:**
  ```json
  {
    "status": "healthy",
    "soulseek_connected": true
  }
  ```

#### `GET /download-dir`

- **Purpose:** Get configured download directory path
- **Returns:** `{"download_dir": "/path/to/downloads"}`

#### `GET /play-file/{file_name}`

- **Purpose:** Stream audio file for playback
- **Path Parameters:**
  - `file_name` (str): File name in download directory
- **Returns:** Audio file as stream
- **Supported Formats:** MP3, WAV, FLAC, M4A, AAC, OGG, OPUS, WMA
- **Status Codes:**
  - 200: File stream
  - 404: File not found

#### `POST /show-in-explorer`

- **Purpose:** Open file location in system file explorer
- **Request Body:** ShowInExplorerRequest
  ```json
  {
    "filePath": "song.mp3"
  }
  ```
- **Returns:** `{"message": "File shown in explorer", "file_path": "/path/to/file"}`
- **Platforms:** Windows (explorer), macOS (Finder), Linux (default manager)

#### `GET /sharing/status`

- **Purpose:** Get sharing configuration and statistics
- **Returns:**
  ```json
  {
    "sharing_enabled": true,
    "sharing_downloads": true,
    "shared_folders": [["Downloads", "/path/to/downloads"]],
    "download_dir": "/path/to/downloads",
    "shared_files_count": 150,
    "total_shared_size": 500000000,
    "upload_slots": 3,
    "rescan_on_startup": true,
    "rescan_daily": true
  }
  ```

#### `POST /sharing/rescan`

- **Purpose:** Manually trigger shared folder rescan
- **Returns:** `{"message": "Share rescan initiated via slskd"}`

#### `GET /connection/status`

- **Purpose:** Get detailed connection status
- **Returns:**
  ```json
  {
    "logged_in": true,
    "username": "sonosano_user",
    "server_address": "slskd",
    "port_range": [2234, 2240],
    "upnp_enabled": true,
    "interface": ""
  }
  ```

#### `POST /romanize`

- **Purpose:** Romanize text (convert non-Latin characters)
- **Request Body:** RomanizeRequest
  ```json
  {
    "text": "日本語"
  }
  ```
- **Returns:**
  ```json
  {
    "romanized_text": "nihongo"
  }
  ```

#### `GET /cover/{image_path}`

- **Purpose:** Serve cover image
- **Path Parameters:**
  - `image_path` (str): Path relative to covers directory
- **Returns:** Image file
- **Status Codes:**
  - 200: Image file
  - 404: Image not found

#### `GET /config`

- **Purpose:** Get application configuration
- **Returns:**
  ```json
  {
    "dataPath": "/path/to/data"
  }
  ```

#### `POST /config`

- **Purpose:** Update application configuration
- **Request Body:** ConfigRequest
  ```json
  {
    "dataPath": "/new/path/to/data"
  }
  ```
- **Returns:** `{"message": "Configuration saved. Please restart the application..."}`

---

## Library Service

**Location:** `backend/src/core/library_service.py`

**Purpose:** Manage local music library database

### Key Methods

#### `get_all_songs() -> List[Dict]`

- **Returns:** All songs in database
- **Song Dictionary Keys:** 'path', 'title', 'artist', 'album', 'duration', 'metadata', etc.

#### `add_or_update_song(song_data: Dict)`

- **Purpose:** Add or update a song in the library
- **Parameters:**
  - `song_data`: Dictionary with song information
- **Updates by:** Song path (unique key)

#### `remove_song(file_path: str)`

- **Purpose:** Remove song from library
- **Parameters:**
  - `file_path`: Path of song to remove

#### `get_lyrics(file_path: str) -> Dict`

- **Purpose:** Get cached lyrics for a song
- **Parameters:**
  - `file_path`: Path of song

#### `upsert_lyrics(lyrics_data: Dict, file_path: str)`

- **Purpose:** Update or insert lyrics
- **Parameters:**
  - `lyrics_data`: Lyrics dictionary
  - `file_path`: Associated song path

---

## Data Models

**Location:** `backend/src/models/`

### search_models.py

#### `SearchQuery`

```python
{
    "artist": str,      # Optional artist name
    "song": str,        # Optional song name
    "query": str        # Full search query
}
```

#### `SearchResult`

```python
{
    "path": str,            # File path on user's system
    "size": int,            # File size in bytes
    "username": str,        # Uploader username
    "extension": str,       # File extension (.mp3, etc.)
    "bitrate": Optional[int],
    "quality": Optional[str],
    "length": Optional[str]
}
```

### download_models.py

#### `DownloadRequest`

```python
{
    "username": str,
    "file_path": str,
    "size": int,
    "metadata": Optional[Dict]
}
```

#### `DownloadStatus`

```python
{
    "status": str,                  # 'Queued', 'Downloading', 'Finished', etc.
    "progress": int,                # Bytes downloaded
    "total": int,                   # Total file size
    "percent": float,               # Percentage (0-100)
    "speed": int,                   # Bytes/sec
    "queuePosition": Optional[int],
    "errorMessage": Optional[str]
}
```

#### `DownloadsAndStatusResponse`

```python
{
    "downloads": List[DownloadStatus],
    "system_status": SystemStatus
}
```

### system_models.py

#### `SystemStatus`

```python
{
    "backend_status": str,          # 'Online', 'Offline'
    "soulseek_status": str,         # 'Connected', 'Disconnected'
    "soulseek_username": Optional[str],
    "active_uploads": int,
    "active_downloads": int
}
```

---

## Quick Reference: Method Call Flow

### Search Flow

1. Frontend calls `POST /search/soulseek` with artist/song
2. Route calls `slskd_manager.perform_search()`
3. Returns search token
4. Frontend polls `GET /search/soulseek/results/{token}` repeatedly
5. Results accumulated in `slskd_manager.search_results[token]`
6. Background thread updates results via `_poll_search_results()`

### Download Flow

1. Frontend calls `POST /download` with username + file_path
2. Route calls `slskd_manager.download_file()`
3. Returns download ID
4. Frontend polls `GET /download-status/{username}/{file_path}`
5. Background thread updates progress via `_monitor_download()`
6. Status accumulated in `slskd_manager.download_status[download_id]`

### Startup Flow

1. `main.py` instantiates SlskcManager
2. Calls `slskd_manager.initialize_slskd()`
3. Authenticates via `_login_to_slskd()`
4. Waits for login via `wait_for_login()`
5. Starts background file watching
6. Returns 200 on `/health` endpoint
