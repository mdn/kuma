CREATE USER 'kuma_ro'@'%' IDENTIFIED BY 'kuma';
GRANT SELECT ON developer_mozilla_org.* TO 'kuma_ro'@'%';
