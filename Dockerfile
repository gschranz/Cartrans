# Website (Caddy) plus kleiner Dienst für Anfragen, Klickzählung und Checkliste (Python, nur Standardbibliothek)
FROM caddy:2-alpine
RUN apk add --no-cache python3
WORKDIR /srv
COPY . /srv
# Ablage: auf Railway ein Volume unter /data einhängen, sonst sind Anfragen und Haken nach jedem Deploy weg
ENV DATA_DIR=/data API_PORT=8081
CMD ["/bin/sh", "/srv/start.sh"]
