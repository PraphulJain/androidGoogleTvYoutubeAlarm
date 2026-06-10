"""
TV Controller using ADB for Google TV
"""
import subprocess
import random
import os
import time
import re
from typing import Optional

from .logger import logger
from .database import get_setting


class TVController:
    """Control Google TV via ADB"""
    
    def __init__(self):
        self.tv_ip = os.getenv("TV_IP", "")
        self.tv_port = os.getenv("TV_PORT", "5555")
        self.device = f"{self.tv_ip}:{self.tv_port}"
    
    def pair(self, pairing_port: str, pairing_code: str) -> bool:
        """Pair with TV using pairing code"""
        if not self.tv_ip:
            logger.error("TV_IP not configured")
            return False
        
        try:
            # adb pair ip:pairing_port pairing_code
            result = subprocess.run(
                ["adb", "pair", f"{self.tv_ip}:{pairing_port}", pairing_code],
                capture_output=True,
                text=True,
                timeout=30
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Successfully paired with TV at {self.tv_ip}:{pairing_port}")
            else:
                logger.error(f"Failed to pair with TV: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"ADB pair error: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to TV via ADB"""
        if not self.tv_ip:
            logger.error("TV_IP not configured")
            return False
        
        try:
            result = subprocess.run(
                ["adb", "connect", self.device],
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Connected to TV at {self.device}")
            else:
                logger.error(f"Failed to connect to TV: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"ADB connect error: {e}")
            return False
    
    def wake_up(self) -> bool:
        """Wake up TV from standby mode"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", "input", "keyevent", "KEYCODE_WAKEUP"],
                capture_output=True,
                text=True,
                timeout=5
            )
            success = result.returncode == 0
            if success:
                logger.info("Sent wake up command to TV")
            else:
                logger.error(f"Failed to wake TV: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Failed to wake up TV: {e}")
            return False
    
    def get_current_volume(self) -> Optional[int]:
        """Get current volume level"""
        try:
            # adb -s ip:port shell cmd media_session volume --stream 3 --get
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", "cmd", "media_session", "volume", "--stream", "3", "--get"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Log full output for debugging
            logger.info(f"Volume command stdout: {result.stdout.strip()}")
            
            if result.returncode == 0 and result.stdout:
                # Parse volume from output - look specifically for "volume is X" pattern
                match = re.search(r'volume is (\d+)', result.stdout)
                if match:
                    volume = int(match.group(1))
                    logger.info(f"Parsed current volume: {volume}")
                    return volume
                else:
                    logger.error(f"Could not parse volume from output: {result.stdout.strip()}")
                    return None
            
            logger.error(f"Failed to get volume - returncode: {result.returncode}, stderr: {result.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return None
    
    def volume_up(self, times: int = 1) -> bool:
        """Press volume up button"""
        try:
            # adb -s ip:port shell "cmd audio set-stream-mute 3 true && for i in {times}; do input keyevent KEYCODE_VOLUME_UP; done"
            command = f'cmd audio set-stream-mute 3 true && for i in {{1..{times}}}; do input keyevent KEYCODE_VOLUME_UP; done'
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Pressed volume up {times} times")
            else:
                logger.error(f"Failed to press volume up: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Error pressing volume up: {e}")
            return False
    
    def volume_down(self, times: int = 1) -> bool:
        """Press volume down button"""
        try:
            # adb -s ip:port shell "cmd audio set-stream-mute 3 true && for i in {times}; do input keyevent KEYCODE_VOLUME_DOWN; done"
            command = f'cmd audio set-stream-mute 3 true && for i in {{1..{times}}}; do input keyevent KEYCODE_VOLUME_DOWN; done'
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Pressed volume down {times} times")
            else:
                logger.error(f"Failed to press volume down: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Error pressing volume down: {e}")
            return False
    
    def set_volume(self, target_volume: int) -> bool:
        """Set volume to target level"""
        try:
            current_volume = self.get_current_volume()
            if current_volume is None:
                logger.error("Could not get current volume")
                return False
            
            difference = target_volume - current_volume
            if difference == 0:
                logger.info(f"Volume already at target level: {target_volume}")
                return True
            
            # Each press changes volume by 2
            presses_needed = abs(difference) // 2
            
            if presses_needed == 0:
                logger.info(f"Volume difference too small to adjust (diff: {difference})")
                return True
            
            logger.info(f"Adjusting volume from {current_volume} to ~{target_volume} ({presses_needed} presses)")
            
            if difference > 0:
                # Need to increase volume
                for i in range(presses_needed):
                    self.volume_up(1)
                    if i < presses_needed - 1:  # Don't wait after last press
                        time.sleep(2)
            else:
                # Need to decrease volume
                for i in range(presses_needed):
                    self.volume_down(1)
                    if i < presses_needed - 1:  # Don't wait after last press
                        time.sleep(2)
            
            logger.info(f"Volume adjustment complete")
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def play_youtube_video(self, video_url: str) -> bool:
        """Play a YouTube video on TV"""
        try:
            # adb -s ip:port shell am start -a android.intent.action.VIEW "url"
            result = subprocess.run(
                [
                    "adb", "-s", self.device, "shell", "am", "start",
                    "-a", "android.intent.action.VIEW",
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Playing YouTube video: {video_url}")
            else:
                logger.error(f"Failed to play video: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Failed to play YouTube video: {e}")
            return False
    
    def trigger_alarm(self, video_url: str) -> bool:
        """
        Complete alarm trigger sequence:
        1. Connect to TV
        2. Wake up TV
        3. Wait 30 seconds
        4. Adjust volume to target
        5. Play video
        """
        try:
            # Step 1: Connect
            logger.info("Step 1: Connecting to TV...")
            if not self.connect():
                logger.error("Failed to connect to TV")
                return False
            
            # Step 2: Wake up
            logger.info("Step 2: Waking up TV...")
            self.wake_up()
            
            # Step 3: Wait 120 seconds
            logger.info("Step 3: Waiting 120 seconds for TV to fully wake up...")
            time.sleep(120)
            
            # Step 4: Set volume
            logger.info("Step 4: Adjusting volume...")
            target_volume_str = get_setting("target_volume")
            if target_volume_str:
                target_volume = int(target_volume_str)
                self.set_volume(target_volume)
            else:
                logger.warning("No target volume set, skipping volume adjustment")
            
            # Step 5: Play video
            logger.info("Step 5: Playing YouTube video...")
            return self.play_youtube_video(video_url)
        except Exception as e:
            logger.error(f"Alarm trigger failed: {e}")
            return False
