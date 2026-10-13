# Hosting on aksanintelligency.sbs

You need: a Linux VPS (2 vCPU / 4 GB RAM minimum, 20 GB+ disk; the embedding
model and torch are heavy) and access to the domain's DNS settings.

## 1. Point the domain at the server
At your domain registrar's DNS panel add:

| Type | Name | Value            |
|------|------|------------------|
| A    | @    | `<server IP>`    |
| A    | www  | `<server IP>`    |

Wait until `nslookup aksanintelligency.sbs` shows the server IP.

## 2. Prepare the server (Ubuntu example)
```bash
curl -fsSL https://get.docker.com | sh
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

## 3. Deploy
```bash
git clone https://github.com/santhoshkumarkandhasamy-coder/hybrid-rag.git
cd hybrid-rag
git checkout claude/funny-fermat-7u2p7u
cp .env.example .env
nano .env     # set DOMAIN, a STRONG ADMIN_PASSWORD, keep ALLOW_SIGNUP=false
docker compose -f docker-compose.prod.yml up -d --build
```
Open https://aksanintelligency.sbs - the HTTPS certificate is issued
automatically on first visit (ports 80 and 443 must be reachable).

## 4. After first login
- Change the admin password (Account page) - never keep a short/default one.
- Create users in Admin Panel -> Users. Leave self sign-up off unless needed.

## Operations
- Logs: `docker compose -f docker-compose.prod.yml logs -f backend`
- Update: `git pull && docker compose -f docker-compose.prod.yml up -d --build`
- **Backups:** everything (users, files, indexes, graph) lives in `./data`.
  Back it up regularly, e.g. `tar czf backup-$(date +%F).tgz data`.
- Only ports 80/443 are public; the API and UI are not exposed directly.
