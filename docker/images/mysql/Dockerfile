FROM mysql:5.6

MAINTAINER MDN Developer <dev-mdn@lists.mozilla.org>
ENV MYSQL_ROOT_PASSWORD kuma
RUN sed -Ei 's/\[mysqld\]/[mysqld]\nmax_allowed_packet=100M\ninnodb_log_file_size=1G/' /etc/mysql/my.cnf
COPY Index.xml /usr/share/mysql/charsets/
EXPOSE 3306:3306
