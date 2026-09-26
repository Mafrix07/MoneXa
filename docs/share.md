# Partager MONEXA avec l'équipe

Nginx est la porte d'entrée unique (port 80). PostgreSQL et Redis restent sur localhost.

## A. Même Wi‑Fi (amphis, coloc, hotspot)

Django doit écouter sur toutes les interfaces (pas seulement 127.0.0.1) :

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Dans un second terminal :

```powershell
docker compose -f docker-compose.gateway.yml up
```

Donne à tes camarades : `http://VOTRE_IP/`  
Exemple : `http://192.168.1.24/`

Si Docker n'est pas installé, Nginx Windows portable :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\share.ps1 -Start
```

Le script télécharge Nginx dans `tools/nginx/` (non versionné) et écoute sur le port 80 vers Django `:8000`.

Pour trouver l'IP :

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -ne 'WellKnown' }
```

Ouvre aussi le pare-feu Windows (réseau privé) pour le port 80 si le navigateur des autres reste bloqué.

Dans `backend/.env` :

```
ALLOWED_HOSTS=*
```

(`DEBUG=True` uniquement pour cette démo.)

## B. Lien Internet (camarades ailleurs)

Le PC doit rester allumé, Django + Nginx lancés, puis Cloudflare Tunnel :

```powershell
docker compose -f docker-compose.gateway.yml --profile share up
```

Sans Docker, installe [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) puis :

```powershell
cloudflared tunnel --url http://127.0.0.1:80
```

(Si Nginx n'est pas lancé : `cloudflared tunnel --url http://127.0.0.1:8000`)

Dans les logs, Cloudflare affiche un URL du type :

```
https://xxxxx.trycloudflare.com
```

C'est ce lien que tu envoies. Il expire à l'arrêt du tunnel.

## C. Stack Docker complète (Postgres + Django + Nginx)

```powershell
docker compose up --build -d
```

Accès : `http://localhost/` (Nginx) — Django n'est plus exposé publiquement sur 8000.

## Compte démo

Uniquement si tu as lancé `seed_demo` :

- Gérant : `gerant@monexa.tg` / `Monexa2026!`

Ne pas utiliser ces identifiants en production.
