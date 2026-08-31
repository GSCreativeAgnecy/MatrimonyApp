# Nginx reverse proxy with the Matchmaking routing baked in.
# Built instead of bind-mounting a config file so it works on any deploy
# platform (file bind mounts break on some hosts — e.g. Coolify).
FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
