FROM debian:jessie

ARG REVISION_HASH
# Make the git commit hash permanently available within this image.
ENV REVISION_HASH $REVISION_HASH

# First install curl so we can use it to get the Node.js debian package.
RUN apt-get update && apt-get install -y curl
# We need "python" and "build-essential" for building "node-gyp".
RUN apt-get update && \
    apt-get install -y --no-install-recommends python2.7 build-essential
# Install the Node.js 6.9.2 LTS release.
ENV DEB_PKG=nodejs_6.9.2-1nodesource1~jessie1_amd64.deb
RUN curl -sLO https://deb.nodesource.com/node_6.x/pool/main/n/nodejs/${DEB_PKG}\
    && dpkg -i ${DEB_PKG} \
    && rm ${DEB_PKG} \
    && apt-get install -f

RUN useradd -m kumascript

WORKDIR /

# Install the Node.js dependencies, but only the versions specified in the
# "npm-shrinkwrap.json" file (if it exists).
COPY kumascript/package.json kumascript/npm-shrinkwrap.json /
RUN npm install
# Update any top-level npm packages listed in package.json,
# as allowed by each package's given "semver".
RUN npm update
ENV NODE_PATH=/node_modules
RUN chown -R kumascript:kumascript $NODE_PATH

# Install the locale files
WORKDIR /locale
COPY locale ./
RUN chown -R kumascript:kumascript .

WORKDIR /app
COPY kumascript ./

# The following is needed until the --user flag is added to COPY
# (see https://github.com/docker/docker/pull/28499).
RUN chown -R kumascript:kumascript .
USER kumascript

CMD ["node", "run.js"]

EXPOSE 9080
