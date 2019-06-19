FROM node:10.16.0@sha256:faf7dd4a26460ac70e3fe591752548003f0f38b3d4021ad2496accf73685219d

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        mime-support \
        build-essential \
        python2.7 \
        default-jre \
    && rm -rf /var/lib/apt/lists/*

# remove the node user from the base package and add a non-privileged user
RUN userdel --force --remove node && \
    adduser --uid 1000 --disabled-password --gecos '' --no-create-home kumascript

ARG REVISION_HASH
# make the git commit hash permanently available within this image.
ENV REVISION_HASH $REVISION_HASH

WORKDIR /

COPY kumascript/package.json kumascript/npm-shrinkwrap.json /
RUN npm config set python /usr/bin/python2.7 && \
    # install the Node.js dependencies,
    # with versions specified in npm-shrinkwrap.json
    npm install && \
    # update any top-level npm packages listed in package.json,
    # such as mdn-browser-compat-data,
    # as allowed by each package's given "semver".
    npm update
ENV NODE_PATH=/node_modules
RUN chown -R kumascript:kumascript $NODE_PATH

# install the locale files
WORKDIR /locale
COPY --chown=kumascript:kumascript locale ./

WORKDIR /app
COPY --chown=kumascript:kumascript kumascript ./

USER kumascript

CMD ["node", "run.js"]

EXPOSE 9080
