import logging
from fastapi import APIRouter, HTTPException
from models.download_models import DownloadRequest, DownloadStatus, DownloadsAndStatusResponse
from models.system_models import SystemStatus
from core.slskd_manager import SlskcManager
import os
import time

router = APIRouter()

slskd_manager: SlskcManager

def _generate_download_id(username: str, file_path: str) -> str:
    """Generates a consistent download ID."""
    return f"{username}:{file_path}"

@router.post("/download")
async def download_file(download_request: DownloadRequest):
    """Download a file from a user."""
    if not slskd_manager.is_logged_in():
        raise HTTPException(status_code=503, detail="Not connected to Soulseek")
    
    try:
        download_id = slskd_manager.download_file(
            username=download_request.username,
            file_path=download_request.file_path,
            size=download_request.size,
            metadata=download_request.metadata
        )
        
        return {"message": "Download started", "download_id": download_id}
    except Exception as e:
        logging.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start download: {str(e)}")

@router.get("/download-status/{username}/{file_path:path}")
async def get_download_status(username: str, file_path: str):
    """Get the status of a download."""
    status = slskd_manager.get_download_status(username, file_path)
    
    return DownloadStatus(
        status=status['status'],
        progress=status['progress'],
        total=status['total'],
        percent=status['percent'],
        speed=status.get('speed', 0),
        queuePosition=status.get('queuePosition'),
        errorMessage=status.get('errorMessage')
    )

@router.get("/downloads/status", response_model=DownloadsAndStatusResponse)
async def get_all_downloads_status():
    """Get the status of all downloads and the system."""
    downloads_list = []
    
    for download_id, download_info in slskd_manager.active_downloads.items():
        status_info = slskd_manager.download_status.get(download_id, {
            'status': 'Queued',
            'progress': 0,
            'total': download_info['size'],
            'percent': 0,
            'speed': 0,
            'queuePosition': None
        })
        
        download_data = {
            'id': download_id,
            'file_name': download_info['file_name'],
            'file_path': download_info['file_path'],
            'path': download_info['file_path'],
            'username': download_info['username'],
            'size': download_info['size'],
            'metadata': download_info.get('metadata'),
            'timestamp': download_info['timestamp'],
            'status': status_info['status'],
            'progress': status_info['progress'],
            'total': status_info['total'],
            'percent': status_info['percent'],
            'speed': status_info.get('speed', 0),
            'queue_position': status_info.get('queuePosition'),
            'error_message': status_info.get('errorMessage'),
            'time_remaining': _calculate_time_remaining(
                status_info['progress'],
                status_info['total'],
                status_info.get('speed', 0)
            ) if status_info.get('speed', 0) > 0 else None
        }
        
        downloads_list.append(download_data)
    
    downloads_list.sort(key=lambda x: x['timestamp'], reverse=True)

    soulseek_status = "Connected" if slskd_manager.is_logged_in() else "Disconnected"
    
    system_status = SystemStatus(
        backend_status="Online",
        soulseek_status=soulseek_status,
        soulseek_username=slskd_manager.username if slskd_manager.is_logged_in() else None,
        active_uploads=0,
        active_downloads=len([d for d in downloads_list if d['status'] == 'Downloading'])
    )
    
    return DownloadsAndStatusResponse(
        downloads=downloads_list,
        system_status=system_status
    )

@router.post("/download/cancel/{download_id:path}")
async def cancel_download(download_id: str):
    """Cancel an active download."""
    from urllib.parse import unquote
    download_id = unquote(download_id)
    
    try:
        parts = download_id.split(':', 1)
        username = parts[0]
        file_path = parts[1]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid download ID format")
    
    if download_id in slskd_manager.active_downloads:
        del slskd_manager.active_downloads[download_id]
    
    if download_id in slskd_manager.download_status:
        del slskd_manager.download_status[download_id]
    
    try:
        # Attempt to cancel via slskd API
        slskd_manager.client.transfers.cancel_download(username, file_path)
    except Exception as e:
        logging.warning(f"Could not cancel via API: {e}")
    
    return {"message": "Download cancelled", "download_id": download_id}

def _calculate_time_remaining(progress: int, total: int, speed: float) -> float:
    """Calculate estimated time remaining for a download."""
    if speed > 0:
        remaining_bytes = total - progress
        return remaining_bytes / speed
    return None