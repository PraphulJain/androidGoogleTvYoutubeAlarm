"""
API Endpoints
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import os
from urllib.parse import unquote
import base64
from datetime import datetime
from zoneinfo import ZoneInfo

from .logger import logger
from .database import (
    create_alarm, get_all_alarms, delete_alarm,
    add_video, get_all_videos, delete_video,
    set_setting, get_setting
)
from .scheduler import scheduler
from .tv_controller import TVController


app = FastAPI(title="Alarm Service API")


def verify_password(password: str) -> bool:
    """Verify password against environment variable"""
    expected = os.getenv("API_PASSWORD", "")
    if not expected:
        logger.warning("API_PASSWORD not set, allowing access")
        return True
    return password == expected


def require_auth(password: Optional[str] = Query(None, alias="pass")):
    """Authentication dependency"""
    if not verify_password(password or ""):
        logger.warning("Authentication failed")
        raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Alarm Backend"}


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/alarms/list")
async def list_alarms(password: Optional[str] = Query(None, alias="pass")):
    """List all alarms with next occurrence"""
    require_auth(password)
    
    try:
        alarms = get_all_alarms()
        
        # Compute next occurrence for each
        now = datetime.now(ZoneInfo("UTC"))
        result = []
        
        for alarm in alarms:
            alarm_data = dict(alarm)
            # Compute next occurrence using scheduler logic
            next_occ = scheduler._compute_next_occurrence(alarm, now)
            alarm_data["next_occurrence"] = next_occ.isoformat() if next_occ else None
            result.append(alarm_data)
        
        logger.info(f"Listed {len(result)} alarms")
        return {"alarms": result, "count": len(result)}
    
    except Exception as e:
        logger.error(f"Error listing alarms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alarms/create_once")
async def create_once_alarm(
    datetime_str: Optional[str] = Query(None, alias="datetime"),
    date: Optional[str] = Query(None),
    time: Optional[str] = Query(None),
    timezone: str = Query("Asia/Kolkata", alias="tz"),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Create one-time alarm
    Parameters:
    - datetime: ISO datetime string (e.g., 2026-06-10T15:30:00)
    - OR date: YYYY-MM-DD and time: HH:MM
    - tz: timezone (default: Asia/Kolkata)
    - pass: password
    """
    require_auth(password)
    
    try:
        # Parse input
        if datetime_str:
            alarm_dt = datetime.fromisoformat(datetime_str)
            alarm_date = alarm_dt.date().isoformat()
            alarm_time = alarm_dt.time().isoformat()
        elif date and time:
            alarm_date = date
            alarm_time = time
        else:
            raise ValueError("Provide either 'datetime' or both 'date' and 'time'")
        
        # Create alarm
        alarm_id = create_alarm(
            alarm_type="one-time",
            time=alarm_time,
            date=alarm_date,
            timezone=timezone
        )
        
        # Notify scheduler
        scheduler.notify_change()
        
        logger.info(f"Created one-time alarm ID {alarm_id}")
        return {"success": True, "id": alarm_id, "type": "one-time"}
    
    except Exception as e:
        logger.error(f"Error creating one-time alarm: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/alarms/create_recurring")
async def create_recurring_alarm(
    time: str = Query(..., description="Time in HH:MM format"),
    days: str = Query("1234567", description="Days string (1=Mon, 7=Sun)"),
    timezone: str = Query("Asia/Kolkata", alias="tz"),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Create recurring alarm
    Parameters:
    - time: HH:MM
    - days: string of digits 1-7 (e.g., "135" for Mon, Wed, Fri)
    - tz: timezone (default: Asia/Kolkata)
    - pass: password
    """
    require_auth(password)
    
    try:
        # Validate days string
        if not all(c in "1234567" for c in days):
            raise ValueError("Days must only contain digits 1-7")
        
        # Create alarm
        alarm_id = create_alarm(
            alarm_type="recurring",
            time=time,
            days=days,
            timezone=timezone
        )
        
        # Notify scheduler
        scheduler.notify_change()
        
        logger.info(f"Created recurring alarm ID {alarm_id}")
        return {"success": True, "id": alarm_id, "type": "recurring", "days": days}
    
    except Exception as e:
        logger.error(f"Error creating recurring alarm: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/alarms/delete")
async def delete_alarm_endpoint(
    id: int = Query(..., description="Alarm ID to delete"),
    password: Optional[str] = Query(None, alias="pass")
):
    """Delete an alarm by ID"""
    require_auth(password)
    
    try:
        success = delete_alarm(id)
        
        if success:
            # Notify scheduler
            scheduler.notify_change()
            logger.info(f"Deleted alarm ID {id}")
            return {"success": True, "deleted_id": id}
        else:
            raise HTTPException(status_code=404, detail=f"Alarm ID {id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alarm: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/list")
async def list_videos(password: Optional[str] = Query(None, alias="pass")):
    """List all video URLs"""
    require_auth(password)
    
    try:
        videos = get_all_videos()
        logger.info(f"Listed {len(videos)} videos")
        return {"videos": videos, "count": len(videos)}
    
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/add")
async def add_video_endpoint(
    url: Optional[str] = Query(None, description="URL-encoded video URL"),
    b64: Optional[str] = Query(None, description="Base64-encoded video URL"),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Add a video URL
    Parameters:
    - url: URL-encoded YouTube URL
    - OR b64: Base64-encoded YouTube URL
    - pass: password
    """
    require_auth(password)
    
    try:
        # Decode URL
        if b64:
            video_url = base64.b64decode(b64).decode('utf-8')
        elif url:
            video_url = unquote(url)
        else:
            raise ValueError("Provide either 'url' or 'b64' parameter")
        
        # Validate YouTube URL
        if not ("youtube.com" in video_url or "youtu.be" in video_url):
            raise ValueError("Must be a YouTube URL")
        
        # Add video
        video_id = add_video(video_url)
        
        if video_id:
            logger.info(f"Added video ID {video_id}")
            return {"success": True, "id": video_id, "url": video_url}
        else:
            return {"success": False, "message": "Video already exists"}
    
    except Exception as e:
        logger.error(f"Error adding video: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/videos/remove")
async def remove_video_endpoint(
    id: Optional[int] = Query(None, description="Video ID to delete"),
    url: Optional[str] = Query(None, description="URL-encoded video URL to delete"),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Remove a video
    Parameters:
    - id: Video ID
    - OR url: URL-encoded video URL
    - pass: password
    """
    require_auth(password)
    
    try:
        if id is None and url is None:
            raise ValueError("Provide either 'id' or 'url' parameter")
        
        decoded_url = unquote(url) if url else None
        success = delete_video(video_id=id, url=decoded_url)
        
        if success:
            logger.info(f"Removed video (ID: {id}, URL: {decoded_url})")
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tv/pair")
async def pair_tv(
    pairing_port: str = Query(..., description="TV pairing port"),
    pairing_code: str = Query(..., description="Pairing code from TV"),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Pair with TV using pairing code
    Parameters:
    - pairing_port: Port shown on TV for pairing
    - pairing_code: 6-digit code shown on TV
    - pass: password
    """
    require_auth(password)
    
    try:
        tv = TVController()
        success = tv.pair(pairing_port, pairing_code)
        
        if success:
            logger.info(f"Successfully paired with TV")
            return {"success": True, "message": "TV paired successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to pair with TV")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pairing TV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tv/volume/set")
async def set_target_volume(
    volume: int = Query(..., description="Target volume level (0-100)", ge=0, le=100),
    password: Optional[str] = Query(None, alias="pass")
):
    """
    Set target volume for alarms
    Parameters:
    - volume: Volume level (0-100)
    - pass: password
    """
    require_auth(password)
    
    try:
        set_setting("target_volume", str(volume))
        logger.info(f"Set target volume to {volume}")
        return {"success": True, "volume": volume}
    
    except Exception as e:
        logger.error(f"Error setting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tv/volume/get")
async def get_target_volume(password: Optional[str] = Query(None, alias="pass")):
    """
    Get current target volume setting
    Parameters:
    - pass: password
    """
    require_auth(password)
    
    try:
        volume_str = get_setting("target_volume")
        if volume_str:
            volume = int(volume_str)
            return {"volume": volume}
        else:
            return {"volume": None, "message": "No target volume set"}
    
    except Exception as e:
        logger.error(f"Error getting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))
