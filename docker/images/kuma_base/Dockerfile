FROM python:2.7-slim-stretch

# Set the environment variables
ENV NODE_VERSION=6.14.2 \
    # extra python env
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # disable this when preparing for Django upgrade
    PYTHONWARNINGS=ignore \
    # Kuma Pipeline definitions
    PIPELINE_CSS_COMPRESSOR=kuma.core.pipeline.cleancss.CleanCSSCompressor \
    PIPELINE_CLEANCSS_BINARY=/usr/local/bin/cleancss \
    PIPELINE_JS_COMPRESSOR=pipeline.compressors.uglifyjs.UglifyJSCompressor \
    PIPELINE_SASS_BINARY=/usr/local/bin/node-sass \
    PIPELINE_UGLIFYJS_BINARY=/usr/local/bin/uglifyjs \
    # gunicorn concurrency
    WEB_CONCURRENCY=4

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        xz-utils \
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
# add node.js 6.x, copied from:
#     https://github.com/nodejs/docker-node/blob/master/6/stretch/Dockerfile
# but with package updates and version definitions moved above
# ----------------------------------------------------------------------------

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
  ; do \
    gpg --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys "$key" || \
    gpg --keyserver hkp://ipv4.pool.sks-keyservers.net --recv-keys "$key" || \
    gpg --keyserver hkp://pgp.mit.edu:80 --recv-keys "$key" ; \
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

# add non-priviledged user
RUN adduser --uid 1000 --disabled-password --gecos '' --no-create-home kuma

WORKDIR /app
EXPOSE 8000

RUN npm install -g \
        fibers@1.0.15 \
        csslint@0.10.0 \
        jshint@2.7.0 \
        node-sass@4.3.0 \
        uglify-js@2.4.13 \
        clean-css@3.4.23 \
        stylelint@7.10.1

COPY ./requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt

# Import issue with configparser 3.5.0
# https://bitbucket.org/ambv/configparser/issues/20/importwarning-missing-__init__py
RUN touch /usr/local/lib/python2.7/site-packages/backports/__init__.py

USER kuma

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout=120", "--worker-class=meinheld.gmeinheld.MeinheldWorker", "kuma.wsgi:application"]
