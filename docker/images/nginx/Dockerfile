FROM nginx

# Creating self signed certificate for localhost
RUN mkdir /etc/nginx/ssl

RUN openssl req \
        -x509 \
        -nodes \
        -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/server.key \
        -out /etc/nginx/ssl/server.crt \
        -days 1000 \
        -subj "/CN=127.0.0.1"

ADD nginx.conf /etc/nginx/nginx.conf
EXPOSE 80 443
