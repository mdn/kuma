FROM python:2.7-slim@sha256:686bc67cbebf4c4fb0d96d55650d8704d00ccb6b9c6bdd0bee5fad48b827a6cb

# Set the environment variables
ENV NODE_VERSION=10.14.2 \
    # extra python env
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # disable this when preparing for Django upgrade
    PYTHONWARNINGS=ignore \
    # enable this when preparing for Django upgrade
    # PYTHONWARNINGS=all \
    # Kuma Pipeline definitions
    PIPELINE_CSS_COMPRESSOR=kuma.core.pipeline.cleancss.CleanCSSCompressor \
    PIPELINE_CLEANCSS_BINARY=/usr/local/bin/cleancss \
    PIPELINE_CLEANCSS_ARGUMENTS="-O1 --skip-rebase" \
    PIPELINE_JS_COMPRESSOR=pipeline.compressors.uglifyjs.UglifyJSCompressor \
    PIPELINE_SASS_BINARY=/usr/local/bin/node-sass \
    PIPELINE_UGLIFYJS_BINARY=/usr/local/bin/uglifyjs \
    # gunicorn concurrency
    WEB_CONCURRENCY=4

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gpg \
        dirmngr \
        libsasl2-modules \
        gettext \
        mime-support \
        build-essential \
        libtidy-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libjpeg-dev \
        libmagic-dev \
        default-libmysqlclient-dev \
        mysql-client \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------------
# add node.js 10.x, copied from:
#     https://github.com/nodejs/docker-node/blob/master/10/stretch/Dockerfile
# but with:
#  The NODE_VERSION environment variable is set above
#  The node user gets uid/gid 1001 rather than 1000
#  Omit the installation of yarn
# ----------------------------------------------------------------------------

RUN groupadd --gid 1001 node \
  && useradd --uid 1001 --gid node --shell /bin/bash --create-home node

# gpg keys listed at https://github.com/nodejs/node#release-keys
RUN set -ex \
  && for key in \
    94AE36675C464D64BAFA68DD7434390BDBE9B9C5 \
    FD3A5288F042B6850C66B31F09FE44734EB7990E \
    71DCFD284A79C3B38668286BC97EC7A07EDE3FC1 \
    DD8F2338BAE7501E3DD5AC78C273792F7D83545D \
    C4F0DFFF4E8C1A8236409D08E73BC641CC11F4C8 \
    B9AE9905FFD7803F25714661B63B535A4C206CA9 \
    56730D5401028683275BD23C23EFEFE93C4CFFFE \
    77984A986EBC2AA786BC0F66B01FBB92821C587A \
    8FCCA13FEF1D0C2E91008E09770F7A9A5AE15600 \
  ; do \
    gpg --batch --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys "$key" || \
    gpg --batch --keyserver hkp://ipv4.pool.sks-keyservers.net --recv-keys "$key" || \
    gpg --batch --keyserver hkp://pgp.mit.edu:80 --recv-keys "$key" ; \
done

RUN ARCH=  && dpkgArch="$(dpkg --print-architecture)" \
    && case "${dpkgArch##*-}" in \
      amd64) ARCH='x64';; \
      ppc64el) ARCH='ppc64le';; \
      s390x) ARCH='s390x';; \
      arm64) ARCH='arm64';; \
      armhf) ARCH='armv7l';; \
      i386) ARCH='x86';; \
      *) echo "unsupported architecture"; exit 1 ;; \
    esac \
    && curl -fsSLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && curl -fsSLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt.asc" \
    && gpg --batch --decrypt --output SHASUMS256.txt SHASUMS256.txt.asc \
    && grep " node-v$NODE_VERSION-linux-$ARCH.tar.xz\$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C /usr/local --strip-components=1 --no-same-owner \
    && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" SHASUMS256.txt.asc SHASUMS256.txt \
    && ln -s /usr/local/bin/node /usr/local/bin/nodejs
# ----------------------------------------------------------------------------

# add non-privileged user
RUN useradd --uid 1000 --shell /bin/bash --create-home kuma \
    && mkdir -p app \
    && chown kuma:kuma /app \
    && chmod 775 /app

# install Python libraries
WORKDIR /app
COPY --chown=kuma:kuma ./requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt

# fix import issue with configparser 3.5.0
# https://bitbucket.org/ambv/configparser/issues/20/importwarning-missing-__init__py
RUN touch /usr/local/lib/python2.7/site-packages/backports/__init__.py

# install Node.js tools
# config files are symlinks to make updating easier
COPY --chown=kuma:kuma ./package.json ./package-lock.json /app/
RUN mkdir /tools \
    && chown kuma:kuma /tools \
    && chmod 775 /tools
WORKDIR /tools
USER kuma
RUN ln -s /app/package.json /tools \
    && ln -s /app/package-lock.json /tools \
    && npm install
USER root
RUN find /tools/node_modules/.bin/ -executable -type f -o -type l -exec ln -s {} /usr/local/bin/ \;
ENV NODE_PATH=/tools/node_modules

# setup default run parameters
USER kuma
WORKDIR /app
EXPOSE 8000
