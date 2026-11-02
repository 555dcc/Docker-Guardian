# 🛡️ Docker Guardian

**A lightweight, self-hosted alternative to Watchtower with auto-rollback and volume backups. Runs perfectly on ARM64 devices (like rooted Android phones or Raspberry Pi).**

## 😫 Why I built this
Watchtower is great, but it blindly updates containers. If an update breaks (config changes, OOM, etc.), your service goes down. For self-hosters, downtime is a nightmare. 

## ✨ Features
- **Zero Cost:** Run it on an old rooted Android phone (via DroidVM) or any Linux server.
- **Web UI:** A beautiful "Black & Gold" dashboard to monitor all your containers.
- **Auto-Rollback:** Failsafe mechanism to prevent downtime. Checks container status 10s after update and reverts if it crashes.
- **Volume Backups:** Automatically tars and saves your critical data (keeps only the last 3).
- **Telegram Alerts:** (Optional) Get notified when things go wrong.

## 🛠️ Quick Start
1. Clone this repo.
2. Build the image: `docker build -t my-guardian:v1 .`
3. Run it: 
```bash
docker run -d --name guardian-web -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock:ro my-guardian:v1
