FROM nginx:1.22

RUN apt-get update \
    && apt-get install -y nginx-extras \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY GeoLite2-Country.mmdb /etc/nginx/GeoLite2-Country.mmdb
