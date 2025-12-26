# Sonosano Backend Migration: Pynicotine → Slskd API

## Summary
The Sonosano backend has been successfully migrated from using **Pynicotine** (Nicotine+ fork) to **slskd-api** for Soulseek network integration.

## Changes Made

### 1. **Dependencies Updated** (`requirements.txt`)
- **Added**: `slskd-api` - Python wrapper for the slskd server API
- **Added**: `python-dotenv` - For environment variable management
- **Removed**: Implicit pynicotine dependency

### 2. **New Manager Created** (`core/slskd_manager.py`)
Replaced the old `SoulseekManager` with a new `SlskcManager` that uses slskd-api:
- Initializes and connects to slskd server
- Manages search operations with background polling
- Handles downloads with progress monitoring
- Supports metadata tracking
- Thread-safe operations with daemon threads

**Key Features:**
- Uses `SlskdClient` from `slskd_api` library
- Reads credentials from `.env` file (USERNAME, PASSWORD, APIKEY)
- Configurable slskd URL via `SLSKD_URL` env var (defaults to `http://localhost:5030`)
- Download directory: `{data_path}/downloads`

### 3. **API Routes Updated**

#### `api/search_routes.py`
- Removed pynicotine event processing
- Updated to use `SlskcManager.perform_search()`
- Simplified search result handling
- Updated connection status checks

#### `api/download_routes.py`
- Removed pynicotine core transfers management
- Updated to use `SlskcManager.download_file()`
- Simplified download status reporting
- Updated cancellation logic for slskd API

#### `api/system_routes.py`
- Removed all pynicotine configuration references
- Simplified sharing status endpoint
- Updated connection diagnostics
- Downloads now always point to `{data_path}/downloads`

### 4. **Main Application Updated** (`main.py`)
- Removed pynicotine config initialization
- Removed misc.json credential management (now handled by .env)
- Replaced `SoulseekManager` with `SlskcManager`
- Simplified startup sequence
- Removed event processing thread (slskd handles this)
- Updated path references for downloads directory

### 5. **Library Service Updated** (`core/library_service.py`)
- Removed pynicotine config import

### 6. **Files Removed**
- `backend/src/pynicotine/` directory (entire folder deleted)
- `core/soulseek_manager.py` (replaced with slskd_manager.py)

## Environment Configuration

Update your `.env` file with:
```env
USERNAME=your_soulseek_username
PASSWORD=your_soulseek_password
APIKEY=your_slskd_api_key
SLSKD_URL=http://localhost:5030
```

## Architecture Changes

### Old Flow (Pynicotine):
```
Sonosano ← → Pynicotine Core (embedded Soulseek client)
            ↓
            Soulseek Network
```

### New Flow (Slskd):
```
Sonosano ← → Slskd Server API (HTTP)
            ↓
            Slskd Daemon ← → Soulseek Network
```

## Benefits of Migration

1. **Decoupled Architecture**: Slskd server runs independently, reducing complexity
2. **HTTP API**: Standard REST/HTTP interface instead of event-based system
3. **Better Performance**: Dedicated server can handle more concurrent operations
4. **Easier Debugging**: Standard HTTP requests/responses
5. **Simpler Dependencies**: No large embedded client library
6. **Configuration**: External slskd server with its own configuration

## Important Notes

1. **Slskd Server Required**: Ensure slskd is running and accessible at the configured URL
2. **API Key**: You must have a valid slskd API key configured
3. **Download Directory**: All downloads are now stored in `{data_path}/downloads`
4. **Shared Folder**: The downloads folder is automatically configured as shared with slskd

## Testing

To verify the migration:
```bash
cd backend/src
python -c "from core.slskd_manager import SlskcManager; print('SlskcManager import successful')"
python -c "from api import search_routes, download_routes, system_routes; print('All API routes imported successfully')"
```

## Next Steps

1. Install slskd server if not already running
2. Configure slskd with proper API key
3. Update `.env` with correct credentials
4. Run the Sonosano backend normally
5. Monitor logs for any connection issues

## Migration Checklist

- [x] Replace Pynicotine with slskd-api
- [x] Create SlskcManager class
- [x] Update all API routes
- [x] Remove pynicotine imports
- [x] Update main.py initialization
- [x] Add .env configuration support
- [x] Update requirements.txt
- [x] Test imports and basic functionality
