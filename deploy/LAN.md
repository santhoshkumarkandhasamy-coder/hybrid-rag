# Internal server (LAN) setup

Goal: run on one machine ("the server"); clients on your network open it in a browser.
Nothing needs the internet except the very first model download (can be pre-copied).

## 1. Give the server a fixed address
Set a static IP (or a DHCP reservation in your router), e.g. `192.168.1.50`.
Optional: add a DNS/hosts name, e.g. `rag.company.local -> 192.168.1.50`.

## 2. Start it
- **Windows:** double-click `run_server.bat`
- **Linux/Mac:** `./run_server.sh`
- **Docker:** `docker compose up -d --build` (only port 8501 is published)

It prints the address clients should open, e.g. `http://192.168.1.50:8501`.
The API (port 8000) is bound to the server itself and is NOT reachable by clients.

## 3. Allow clients through the firewall (server)
**Windows (run PowerShell as Administrator):**
```powershell
New-NetFirewallRule -DisplayName "Hybrid RAG" -Direction Inbound -Protocol TCP -LocalPort 8501 -Action Allow -Profile Private,Domain
```
**Ubuntu:** `sudo ufw allow from 192.168.1.0/24 to any port 8501`
(restrict to your LAN subnet).

## 4. Create accounts for clients
Sign in as `admin` -> Admin Panel -> Users -> create one account per client
(role `user`, set a storage quota). Keep self sign-up OFF.
Each client only ever sees their own files.

## 5. Keep it running after reboot
- **Windows:** Task Scheduler -> Create Task -> "Run whether user is logged on or not",
  trigger "At startup", action: `C:\path\to\hybrid-rag\run_server.bat`.
- **Linux:** use Docker (`restart: unless-stopped` is already set) or a systemd unit.

## 6. (Recommended) HTTPS inside the network
Plain `http://` sends passwords unencrypted across the LAN. For HTTPS:
```bash
# .env
DOMAIN=rag.company.local          # or the server IP
CADDYFILE=./deploy/Caddyfile.lan
docker compose -f docker-compose.prod.yml up -d --build
```
Clients open `https://rag.company.local`. Each client must trust Caddy's root
certificate once: copy it from the server
(`docker cp hybrid-rag-caddy:/data/caddy/pki/authorities/local/root.crt .`)
and install it as a Trusted Root CA (double-click on Windows).

## Capacity tips
- 8 GB RAM / 4 cores handles a small team; the embedding model uses ~1 GB.
- Back up the `data` folder (users, files, indexes) regularly.
- Change the admin password from the Account page after first login.
