"""
Alarm Scheduler Service - Single timer approach
"""
import asyncio
from datetime import datetime, timedelta, time as dt_time
from typing import Optional, Dict, Any
import random
from zoneinfo import ZoneInfo

from .logger import logger
from .database import get_all_alarms, delete_alarm, get_all_videos
from .tv_controller import TVController


class AlarmScheduler:
    """Single-timer alarm scheduler"""
    
    def __init__(self):
        self.tv_controller = TVController()
        self.running = False
        self.wake_event = asyncio.Event()
        self.scheduler_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Alarm scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.wake_event.set()
        if self.scheduler_task:
            await self.scheduler_task
        logger.info("Alarm scheduler stopped")
    
    def notify_change(self):
        """Notify scheduler of alarm changes (create/delete)"""
        self.wake_event.set()
    
    async def _scheduler_loop(self):
        """Main scheduler loop - waits for next alarm"""
        while self.running:
            try:
                next_alarm = self._get_next_alarm()
                
                if next_alarm is None:
                    # No alarms, wait indefinitely until notified
                    logger.info("No alarms scheduled, waiting...")
                    await self.wake_event.wait()
                    self.wake_event.clear()
                    continue
                
                alarm_id = next_alarm["id"]
                next_time = next_alarm["next_occurrence"]
                now = datetime.now(ZoneInfo("UTC"))
                
                if next_time <= now:
                    # Alarm is due now
                    await self._trigger_alarm(next_alarm)
                    continue
                
                # Calculate sleep duration
                sleep_seconds = (next_time - now).total_seconds()
                logger.info(f"Next alarm ID {alarm_id} in {sleep_seconds:.1f}s at {next_time.isoformat()}")
                
                # Wait with interrupt capability
                try:
                    await asyncio.wait_for(self.wake_event.wait(), timeout=sleep_seconds)
                    # If we reach here, we were interrupted
                    self.wake_event.clear()
                    logger.info("Scheduler woken up by alarm change")
                except asyncio.TimeoutError:
                    # Timeout means it's time to trigger the alarm
                    await self._trigger_alarm(next_alarm)
            
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    def _get_next_alarm(self) -> Optional[Dict[str, Any]]:
        """Get the next alarm to trigger"""
        alarms = get_all_alarms()
        if not alarms:
            return None
        
        now = datetime.now(ZoneInfo("UTC"))
        candidates = []
        
        for alarm in alarms:
            next_occurrence = self._compute_next_occurrence(alarm, now)
            if next_occurrence:
                candidates.append({
                    **alarm,
                    "next_occurrence": next_occurrence
                })
        
        if not candidates:
            return None
        
        # Return alarm with earliest next occurrence
        return min(candidates, key=lambda a: a["next_occurrence"])
    
    def _compute_next_occurrence(self, alarm: Dict[str, Any], now: datetime) -> Optional[datetime]:
        """Compute next occurrence time for an alarm"""
        try:
            tz = ZoneInfo(alarm.get("timezone", "Asia/Kolkata"))
            
            if alarm["type"] == "one-time":
                # Parse date and time
                alarm_date = datetime.fromisoformat(alarm["date"])
                alarm_time = dt_time.fromisoformat(alarm["time"])
                alarm_dt = datetime.combine(alarm_date.date(), alarm_time, tzinfo=tz)
                
                # Convert to UTC
                alarm_utc = alarm_dt.astimezone(ZoneInfo("UTC"))
                
                # Only return if in future
                if alarm_utc > now:
                    return alarm_utc
                return None
            
            elif alarm["type"] == "recurring":
                # Parse time
                alarm_time = dt_time.fromisoformat(alarm["time"])
                days_str = alarm.get("days", "1234567")
                
                # Convert day numbers to weekday (1=Mon=0, 7=Sun=6)
                active_weekdays = set()
                for day_char in days_str:
                    day_num = int(day_char)
                    if 1 <= day_num <= 7:
                        weekday = (day_num - 1) % 7  # 1->0(Mon), 7->6(Sun)
                        active_weekdays.add(weekday)
                
                if not active_weekdays:
                    return None
                
                # Find next occurrence
                # Start from today in the alarm's timezone
                now_local = now.astimezone(tz)
                current_date = now_local.date()
                
                # Check next 8 days to find a matching weekday
                for days_ahead in range(8):
                    check_date = current_date + timedelta(days=days_ahead)
                    check_weekday = check_date.weekday()
                    
                    if check_weekday in active_weekdays:
                        candidate_dt = datetime.combine(check_date, alarm_time, tzinfo=tz)
                        candidate_utc = candidate_dt.astimezone(ZoneInfo("UTC"))
                        
                        if candidate_utc > now:
                            return candidate_utc
                
                return None
        
        except Exception as e:
            logger.error(f"Error computing next occurrence for alarm {alarm.get('id')}: {e}")
            return None
    
    async def _trigger_alarm(self, alarm: Dict[str, Any]):
        """Trigger an alarm"""
        alarm_id = alarm["id"]
        alarm_type = alarm["type"]
        
        logger.info(f"Triggering alarm ID {alarm_id} (type: {alarm_type})")
        
        try:
            # Get random video
            videos = get_all_videos()
            if not videos:
                logger.error("No videos configured, cannot trigger alarm")
                # Still treat as triggered for cleanup purposes
                if alarm_type == "one-time":
                    delete_alarm(alarm_id)
                return
            
            video = random.choice(videos)
            video_url = video["url"]
            
            logger.info(f"Selected video: {video_url}")
            
            # Trigger TV (run in executor to not block)
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self.tv_controller.trigger_alarm,
                video_url
            )
            
            if success:
                logger.info(f"Alarm ID {alarm_id} triggered successfully")
            else:
                logger.error(f"Alarm ID {alarm_id} trigger failed")
        
        except Exception as e:
            logger.error(f"Error triggering alarm ID {alarm_id}: {e}")
        
        finally:
            # Always delete one-time alarms after trigger (success or failure)
            if alarm_type == "one-time":
                delete_alarm(alarm_id)
                logger.info(f"One-time alarm ID {alarm_id} deleted after trigger")


# Global scheduler instance
scheduler = AlarmScheduler()
