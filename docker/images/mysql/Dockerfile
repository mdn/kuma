FROM mysql:5.6

ENV MYSQL_ROOT_PASSWORD kuma
COPY kuma.cnf /etc/mysql/conf.d/
COPY Index.xml /usr/share/mysql/charsets/
EXPOSE 3306:3306
