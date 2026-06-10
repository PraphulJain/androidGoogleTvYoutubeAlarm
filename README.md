# Android Google TV YouTube Alarm

A Docker-based alarm application that turns on your Google TV and plays a random YouTube video at scheduled times.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # Application entry point
│   │   ├── config.py        # Configuration management
│   │   ├── api.py           # REST API endpoints
│   │   ├── database.py      # SQLite database operations
│   │   ├── scheduler.py     # Single-timer alarm scheduler
│   │   ├── tv_controller.py # ADB TV control
│   │   └── logger.py        # Logtail logging setup
│   └── requirements.txt     # Python dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
└── .env.example           # Environment variables template
```

## Features

- ✅ Docker-based deployment with minimal image size (Python Alpine)
- ✅ ADB toolkit for Google TV control
- ✅ Single-timer scheduler (minimal CPU/memory usage)
- ✅ REST API for alarm management (GET-only endpoints)
- ✅ One-time and recurring alarms
- ✅ Random YouTube video playback
- ✅ TV power control via ADB
- ✅ Logtail integration for remote logging
- ✅ Password protection for all endpoints

## Prerequisites

- Docker and Docker Compose installed
- Google TV with Developer Mode enabled
- Google TV IP address on your local network
- Install ([adb-auto-enable app](https://github.com/mouldybread/adb-auto-enable)) so the wireless debugging will not turn off after some inactivity

## Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure:
   ```bash
   TV_IP=192.168.1.xxx          # Your TV's IP address
   API_PASSWORD=your_password    # Set a secure password
   LOGTAIL_TOKEN=your_token     # Optional: for remote logging
   TZ=America/New_York          # Your timezone
   ```

3. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

4. Check logs:
   ```bash
   docker-compose logs -f
   ```

## Google TV Setup

1. Enable Developer Mode on your Google TV
2. Enable Wireless Debugging in Developer Options
3. Note your TV's IP address from Settings > Network
4. When wireless debugging is enabled, get the pairing port and code from TV
5. Use the pairing API to connect (see API section below)

**Note:** Google TV wireless debugging may disable after inactivity. Use the `/tv/pair` API to re-pair when needed.

## API Usage

All endpoints require the `pass` query parameter with your configured password.

Base URL: `http://localhost:5127`

### Health Check
```
GET /health
```

### List All Alarms
```
GET /alarms/list?pass=YOUR_PASSWORD
```

### Create One-Time Alarm
```
# Using datetime
GET /alarms/create_once?datetime=2026-06-10T15:30:00&pass=YOUR_PASSWORD

# Using separate date and time
GET /alarms/create_once?date=2026-06-10&time=15:30&tz=America/New_York&pass=YOUR_PASSWORD
```

### Create Recurring Alarm
```
# Weekdays only (Mon-Fri at 7:00 AM)
GET /alarms/create_recurring?time=07:00&days=12345&tz=America/New_York&pass=YOUR_PASSWORD

# Every day at 6:30 PM
GET /alarms/create_recurring?time=18:30&days=1234567&pass=YOUR_PASSWORD

# Monday, Wednesday, Friday
GET /alarms/create_recurring?time=08:00&days=135&pass=YOUR_PASSWORD
```

Days parameter: `1`=Monday, `2`=Tuesday, `3`=Wednesday, `4`=Thursday, `5`=Friday, `6`=Saturday, `7`=Sunday

### Delete Alarm
```
GET /alarms/delete?id=1&pass=YOUR_PASSWORD
```

### List Videos
```
GET /videos/list?pass=YOUR_PASSWORD
```

### Add Video
```
# URL-encoded
GET /videos/add?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ&pass=YOUR_PASSWORD

# Base64-encoded (recommended)
GET /videos/add?b64=aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g/dj1kUXc0dzlXZ1hjUQ==&pass=YOUR_PASSWORD
```

### Remove Video
```
# By ID
GET /videos/remove?id=1&pass=YOUR_PASSWORD

# By URL (URL-encoded)
GET /videos/remove?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ&pass=YOUR_PASSWORD
```

### TV Pairing
```
# Pair with TV when wireless debugging resets
GET /tv/pair?pairing_port=12345&pairing_code=123456&pass=YOUR_PASSWORD
```
 (using configured IP and port)
   - Sends wake up command to TV
   - Waits 30 seconds for TV to fully boot
   - Gets current volume level
   - Adjusts volume to target using volume up/down keys (2 points per press, 2 sec between presses)
   - Selects random video from configured list
   - Plays video via YouTube intent
4. **Cleanup**: One-time alarms auto-delete after triggering
5. **Logging**: All events logged to console and Logtail (if configured)
Get the pairing port and 6-digit code from: TV Settings > Developer Options > Wireless Debugging > Pair device

### Set Target Volume
```
# Set volume level for alarms (0-100)
GET /tv/volume/set?volume=30&pass=YOUR_PASSWORD
```

### Get Target Volume
```
GET /tv/volume/get?pass=YOUR_PASSWORD
```

## Architecture

- **Single-Timer Design**: Uses one async wait loop instead of multiple timers, minimizing CPU and memory
- **Non-Blocking**: Async/await throughout, no thread blocking
- **Durable Storage**: SQLite for persistent alarm and video data
- **Error Handling**: Failures logged but treated as successful triggers to prevent alarm hanging
- **Volume Control**: Smart volume adjustment with 2-second delays between presses

## Development

To stop the container:
```bash
docker-compose down
```

To rebuild after code changes:
```bash
docker-compose up -d --build
```

To view logs:
```bash
docker-compose logs -f alarm-backend
```

## Troubleshooting

**Wireless Debugging Disabled:**
- Google TV disables wireless debugging after inactivity
- Use the `/tv/pair` API with new pairing port and code from TV
- Set TV IP as static in router to avoid IP changes

**ADB Connection Issues:**
- Ensure TV and Docker host are on same network
- Try `network_mode: host` in docker-compose.yml (uncomment)
- Verify TV IP address is correct
- Check wireless debugging is enabled on TV
- Re-pair using `/tv/pair` endpoint

**Alarm Not Triggering:**
- Check logs: `docker-compose logs -f`
- Verify videos are configured: `GET /videos/list`
- Ensure timezone is set correctly (e.g., `tz=Asia/Kolkata` for IST)
- Check TV is reachable via ADB
- Set target volume: `GET /tv/volume/set?volume=30`

**API Not Accessible:**
- Verify port 5127 is not in use: `lsof -i :5127`
- Check container is running: `docker ps`
- Ensure password is correct in API calls

## License

See LICENSE file for details.
