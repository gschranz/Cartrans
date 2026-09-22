#!/bin/sh
# Dienst im Hintergrund, Caddy im Vordergrund (Railway beobachtet diesen Prozess)
mkdir -p "${DATA_DIR:-/data}"
python3 /srv/server/api.py &
exec caddy run --config /srv/Caddyfile --adapter caddyfile
