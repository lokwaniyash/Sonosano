import os
import logging
import threading
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict
from slskd_api import SlskdClient
import requests

class SlskcManager:
    def __init__(self, library_service, data_path: str):
        self.library_service = library_service
        self.data_path = data_path
        self.logged_in = False
        self.login_event = threading.Event()
        self.search_results = defaultdict(list)
        self.download_status = {}
        self.search_tokens = {}
        self.active_downloads = {}
        self.next_search_token = 1
        
        # Initialize slskd client
        self.api_key = os.getenv('APIKEY', '')
        self.slskd_url = os.getenv('SLSKD_URL', 'http://localhost:5030')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the slskd API client."""
        try:
            self.client = SlskdClient(self.slskd_url, self.api_key)
            logging.info(f"SlskdClient initialized at {self.slskd_url}")
        except Exception as e:
            logging.error(f"Failed to initialize SlskdClient: {e}")

    def initialize_slskd(self):
        """Initialize and connect to slskd server."""
        try:
            if not self.client:
                self._initialize_client()
            
            # Login to slskd
            self._login_to_slskd()
            self.setup_slskd_config()
            self.logged_in = True
            self.login_event.set()
            logging.info("Successfully initialized slskd")
        except Exception as e:
            logging.error(f"Error initializing slskd: {e}")
            self.logged_in = False

    def _login_to_slskd(self):
        """Authenticate with slskd."""
        try:
            # Check server status
            status = self.client.server.state()
            logging.info(f"Server status: {status}")
            
            if status.get('state') == 'Disconnected':
                # Connect to Soulseek
                connect_response = self.client.server.connect()
                logging.info(f"Connection initiated: {connect_response}")
                
                # Wait for connection
                for _ in range(30):  # 30 second timeout
                    status = self.client.server.state()
                    if status.get('state') == 'Connected':
                        logging.info("Successfully connected to Soulseek")
                        self.logged_in = True
                        return
                    time.sleep(1)
                
                raise Exception("Failed to connect to Soulseek within timeout")
            else:
                self.logged_in = True
                logging.info("Already connected to Soulseek")
        except Exception as e:
            logging.error(f"Login error: {e}")
            raise

    def setup_slskd_config(self):
        """Configure slskd settings."""
        try:
            # Ensure download directory exists locally
            download_dir = os.path.join(self.data_path, "downloads")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            logging.info(f"Local download directory ensured: {download_dir}")
            
            # Note: slskd configuration (like downloadDirectory) is managed through 
            # the slskd.yml config file directly, not through the API.
            # The API options.get() is read-only for most settings.
        except Exception as e:
            logging.warning(f"Could not setup local directory: {e}")

    def perform_search(self, artist: Optional[str], song: Optional[str], raw_query: str) -> tuple[int, str]:
        """Perform a search and return token and query."""
        try:
            token = self.next_search_token
            self.next_search_token += 1
            # Use artist + song if both available, otherwise use raw query
            if artist and song:
                position = artist.find('·')
                if position != -1:
                    fixedArtistString = artist[position + 1:].strip()
                else:
                    fixedArtistString = artist
                search_term = f"{fixedArtistString} {song}"
            else:
                search_term = raw_query
            
            # Perform search with parameters
            search_params = {
                'fileLimit': 20,  # Max 20 files
                # 'maximumPeerQueueLength': 0,
                # 'searchTimeout': 4000  # 4 seconds in milliseconds
            }
            search_response = self.client.searches.search_text(search_term, **search_params)
            
            # Initialize results list for this token
            self.search_results[token] = []
            self.search_tokens[token] = search_term
            
            # Poll for results
            self._poll_search_results(token, search_response.get('id') if search_response else None)
            
            return token, search_term
        except Exception as e:
            logging.error(f"Search error: {e}")
            return None, raw_query

    def _poll_search_results(self, token: int, search_id: Optional[str]):
        """Poll for search results in background."""
        def poll():
            try:
                if not search_id:
                    return
                
                for attempt in range(4):  # Poll for up to 4 seconds (matching timeout)
                    try:
                        responses = self.client.searches.search_responses(search_id)
                        
                        if responses:
                            formatted_results = []
                            
                            for response in responses:
                                # response is a SearchResponseItem with 'files' list
                                files = response.get('files', [])
                                username = response.get('username', '')
                                queue_length = response.get('queueLength', 999)
                                upload_speed = response.get('uploadSpeed', 0)  # bytes/s
                                
                                # Filter by upload speed (minimum 100KB/s = 102400 bytes/s)
                                if upload_speed < 102400:
                                    continue
                                
                                # Only allow queue length of 0
                                if queue_length > 0:
                                    continue
                                
                                for file in files:
                                    # Skip locked files
                                    if file.get('isLocked', False):
                                        continue
                                    
                                    # Check file size (max 25MB)
                                    file_size = file.get('size', 0)
                                    if file_size > 25 * 1024 * 1024:
                                        continue
                                    
                                    # Only allow FLAC, MP3, WAV
                                    extension = self._extract_extension(file.get('filename', ''))
                                    if extension not in ['.flac', '.mp3', '.wav']:
                                        continue
                                    
                                    # Get quality (bitrate as proxy for quality)
                                    bitrate = file.get('bitRate', 0)
                                    
                                    file_info = {
                                        'path': file.get('filename', ''),
                                        'size': file_size,
                                        'extension': extension,
                                        'username': username,
                                        'bitrate': bitrate,
                                        'quality': bitrate,  # Use bitrate as quality metric
                                        'length': self._format_duration(file.get('length', 0)),
                                        'queueCount': queue_length,
                                        'uploadSpeed': upload_speed,
                                        'isLocked': False
                                    }
                                    formatted_results.append(file_info)
                            
                            # Sort results: 
                            # 1. FLAC format first (is_flac = True should be first)
                            # 2. Then highest quality (bitrate) first
                            # 3. Then lowest queue count (for redundancy)
                            def sort_key(item):
                                ext = item.get('extension', '').lower()
                                is_flac = ext == '.flac'
                                bitrate = item.get('bitrate', 0)
                                queue_count = item.get('queueCount', 999)
                                
                                # FLAC priority: 0 (comes first), Others: 1
                                priority = 0 if is_flac else 1
                                # Higher bitrate first (negate to reverse)
                                # Lower queue count first (natural)
                                return (priority, -bitrate, queue_count)
                            
                            formatted_results.sort(key=sort_key)
                            
                            # Limit to 20 results
                            self.search_results[token] = formatted_results[:20]
                        
                        time.sleep(1)
                    except Exception as e:
                        logging.debug(f"Polling attempt {attempt} failed: {e}")
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error polling search results: {e}")
        
        # Start polling in background thread
        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

    def _extract_extension(self, path: str) -> str:
        """Extract file extension from path."""
        if not path:
            return ""
        _, ext = os.path.splitext(path)
        return ext.lower()

    def _format_duration(self, seconds: int) -> str:
        """Convert seconds to MM:SS format."""
        if not seconds or seconds <= 0:
            return "0:00"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    def download_file(self, username: str, file_path: str, size: int, metadata: Optional[Dict] = None) -> str:
        """Download a file and return download ID."""
        try:
            download_id = f"{username}:{file_path}"
            filename = os.path.basename(file_path)
            
            # Store metadata
            if metadata:
                self.library_service.download_metadata[download_id] = metadata
                self.library_service.download_metadata[filename] = metadata
            
            # Track active download
            self.active_downloads[download_id] = {
                'id': download_id,
                'file_name': filename,
                'file_path': file_path,
                'username': username,
                'size': size,
                'metadata': metadata,
                'timestamp': time.time()
            }
            
            # Initiate download via slskd API
            download_response = self.client.transfers.enqueue(
                username=username,
                files=[{
                    'filename': file_path,
                    'size': size,
                    'code': 0,
                    'isLocked': False,
                    'extension': os.path.splitext(file_path)[1]
                }]
            )
            
            # Initialize download status
            self.download_status[download_id] = {
                'status': 'Queued',
                'progress': 0,
                'total': size,
                'percent': 0,
                'speed': 0,
                'queuePosition': None
            }
            
            # Start monitoring download
            self._monitor_download(download_id, username, file_path)
            
            logging.info(f"Download started: {download_id}")
            return download_id
        except Exception as e:
            logging.error(f"Download error for {file_path}: {e}")
            raise

    def _monitor_download(self, download_id: str, username: str, file_path: str):
        """Monitor download progress in background."""
        def monitor():
            try:
                for _ in range(300):  # Monitor for up to 5 minutes
                    try:
                        # Get transfer status from slskd
                        transfer_data = self.client.transfers.get_downloads(username)
                        
                        if transfer_data and transfer_data.get('directories'):
                            for directory in transfer_data.get('directories', []):
                                for transfer in directory.get('files', []):
                                    if transfer.get('filename') == file_path:
                                        status_map = {
                                            'Queued': 'Queued',
                                            'Downloading': 'Downloading',
                                            'Completed': 'Finished',
                                            'Failed': 'Failed',
                                            'Cancelled': 'Cancelled'
                                        }
                                        
                                        status = status_map.get(transfer.get('state', ''), transfer.get('state', 'Unknown'))
                                        progress = transfer.get('bytesTransferred', 0)
                                        total = transfer.get('size', 0)
                                        percent = (progress / total * 100) if total > 0 else 0
                                        speed = transfer.get('averageSpeed', 0)
                                        
                                        self.download_status[download_id] = {
                                            'status': status,
                                            'progress': progress,
                                            'total': total,
                                            'percent': percent,
                                            'speed': speed,
                                            'queuePosition': None
                                        }
                                        
                                        if status in ['Finished', 'Failed', 'Cancelled']:
                                            logging.info(f"Download {download_id} finished with status: {status}")
                                            return
                        
                        time.sleep(1)
                    except Exception as e:
                        logging.debug(f"Monitor iteration failed: {e}")
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error monitoring download: {e}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def get_search_results(self, token: int) -> List[Dict[str, Any]]:
        """Get search results for a token."""
        return self.search_results.get(token, [])

    def get_download_status(self, username: str, file_path: str) -> Dict[str, Any]:
        """Get download status."""
        key = f"{username}:{file_path}"
        return self.download_status.get(key, {
            'status': 'Not started',
            'progress': 0,
            'total': 0,
            'percent': 0,
            'speed': 0,
            'queuePosition': None
        })

    def is_logged_in(self) -> bool:
        """Check if connected to Soulseek."""
        return self.logged_in

    def wait_for_login(self, timeout: int = 30) -> bool:
        """Wait for login completion."""
        return self.login_event.wait(timeout)
