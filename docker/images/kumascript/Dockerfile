FROM node:10.14.2-slim

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        mime-support \
        build-essential \
        python2.7 \
    && rm -rf /var/lib/apt/lists/*

# remove the node user from the base package and add a non-priviledged user
RUN userdel --force --remove node && \
    adduser --uid 1000 --disabled-password --gecos '' --no-create-home kumascript

ARG REVISION_HASH
# make the git commit hash permanently available within this image.
ENV REVISION_HASH $REVISION_HASH

WORKDIR /

# install the Node.js dependencies, but only the versions
# specified in "npm-shrinkwrap.json" (if it exists)
COPY kumascript/package.json kumascript/npm-shrinkwrap.json /
RUN npm config set python /usr/bin/python2.7
RUN npm install
# update any top-level npm packages listed in package.json,
# as allowed by each package's given "semver".
RUN npm update
ENV NODE_PATH=/node_modules
RUN chown -R kumascript:kumascript $NODE_PATH

# install the locale files
WORKDIR /locale
COPY locale ./
RUN chown -R kumascript:kumascript .

WORKDIR /app
COPY kumascript ./

# the following is needed until the --user flag is added to COPY
# (see https://github.com/docker/docker/pull/28499).
RUN chown -R kumascript:kumascript .
USER kumascript

CMD ["node", "run.js"]

EXPOSE 9080
