FROM python:2.7-slim

# extra python env
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# disable this when preparing for Django upgrade
ENV PYTHONWARNINGS=ignore

# ----------------------------------------------------------------------------
# add node.js 6.12, copied from:
#     https://github.com/nodejs/docker-node/blob/master/6.12/slim/Dockerfile
# but with curl added to the list of packages installed.
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
    gpg --keyserver pgp.mit.edu --recv-keys "$key" || \
    gpg --keyserver keyserver.pgp.com --recv-keys "$key" || \
    gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$key" ; \
  done

ENV NODE_VERSION 6.12.0

RUN buildDeps='xz-utils' \
    && ARCH= && dpkgArch="$(dpkg --print-architecture)" \
    && case "${dpkgArch##*-}" in \
      amd64) ARCH='x64';; \
      ppc64el) ARCH='ppc64le';; \
      s390x) ARCH='s390x';; \
      arm64) ARCH='arm64';; \
      armhf) ARCH='armv7l';; \
      i386) ARCH='x86';; \
      *) echo "unsupported architecture"; exit 1 ;; \
    esac \
    && set -x \
    && apt-get update && apt-get install -y curl $buildDeps --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && curl -SLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt.asc" \
    && gpg --batch --decrypt --output SHASUMS256.txt SHASUMS256.txt.asc \
    && grep " node-v$NODE_VERSION-linux-$ARCH.tar.xz\$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C /usr/local --strip-components=1 --no-same-owner \
    && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" SHASUMS256.txt.asc SHASUMS256.txt \
    && apt-get purge -y --auto-remove $buildDeps \
    && ln -s /usr/local/bin/node /usr/local/bin/nodejs

ENV YARN_VERSION 1.3.2

RUN set -ex \
  && for key in \
    6A010C5166006599AA17F08146C2130DFD2497F5 \
  ; do \
    gpg --keyserver pgp.mit.edu --recv-keys "$key" || \
    gpg --keyserver keyserver.pgp.com --recv-keys "$key" || \
    gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$key" ; \
  done \
  && curl -fSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz" \
  && curl -fSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz.asc" \
  && gpg --batch --verify yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz \
  && mkdir -p /opt/yarn \
  && tar -xzf yarn-v$YARN_VERSION.tar.gz -C /opt/yarn --strip-components=1 \
  && ln -s /opt/yarn/bin/yarn /usr/local/bin/yarn \
  && ln -s /opt/yarn/bin/yarn /usr/local/bin/yarnpkg \
  && rm yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz
# ----------------------------------------------------------------------------

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        mime-support \
        build-essential \
        libtidy-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libjpeg-dev \
        libmagic-dev \
        libmysqlclient-dev \
        mysql-client \
    && rm -rf /var/lib/apt/lists/*

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

ENV PIPELINE_CSS_COMPRESSOR=kuma.core.pipeline.cleancss.CleanCSSCompressor \
    PIPELINE_CLEANCSS_BINARY=/usr/local/bin/cleancss \
    PIPELINE_JS_COMPRESSOR=pipeline.compressors.uglifyjs.UglifyJSCompressor \
    PIPELINE_SASS_BINARY=/usr/local/bin/node-sass \
    PIPELINE_UGLIFYJS_BINARY=/usr/local/bin/uglifyjs

COPY ./requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt

# Import issue with configparser 3.5.0
# https://bitbucket.org/ambv/configparser/issues/20/importwarning-missing-__init__py
RUN touch /usr/local/lib/python2.7/site-packages/backports/__init__.py

USER kuma

ENV WEB_CONCURRENCY=4
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout=120", "--worker-class=meinheld.gmeinheld.MeinheldWorker", "kuma.wsgi:application"]
