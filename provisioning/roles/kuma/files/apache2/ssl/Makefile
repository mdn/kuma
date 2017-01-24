generate:
	openssl req -x509 -sha256 \
	-newkey rsa:2048 \
	-keyout apache.key \
	-out apache.crt \
	-days 730 \
	-nodes \
	-config openssl.cnf \
	-subj "/C=US/ST=CA/L=Mountain View/O=Mozilla/OU=MDN/CN=developer-local.allizom.org/emailAddress=mdn-dev@mozilla.com"

print_cert:
	openssl x509 -in apache.crt -text -noout
