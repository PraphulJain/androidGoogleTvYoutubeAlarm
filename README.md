# Android Google TV YouTube Alarm

A Docker-based alarm application that turns on your Google TV and plays a random YouTube video at scheduled times.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # Application entry point
│   │   └── config.py        # Configuration management
│   └── requirements.txt     # Python dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
└── .env.example           # Environment variables template
```

## Features (Planned)

- ✅ Docker-based deployment with minimal image size (Python Alpine)
- ✅ ADB toolkit for Google TV control
- ✅ Timezone support
- 🔲 REST API for alarm management
- 🔲 Alarm scheduling system
- 🔲 Random YouTube video playback
- 🔲 TV power control via ADB

## Prerequisites

- Docker and Docker Compose installed
- Google TV with Developer Mode enabled
- Google TV IP address on your local network

## Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your TV's IP address:
   ```
   TV_IP=192.168.1.xxx
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
2. Enable USB Debugging in Developer Options
3. Note your TV's IP address from Settings > Network
4. Pair ADB (first time only):
   ```bash
   docker-compose exec alarm-backend adb connect <TV_IP>:5555
   ```

## Development

To stop the container:
```bash
docker-compose down
```

To rebuild after code changes:
```bash
docker-compose up -d --build
```

## License

See LICENSE file for details.
