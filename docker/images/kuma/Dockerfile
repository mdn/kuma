FROM mdnwebdocs/kuma_base:latest@sha256:f72cd16767172d465dfbc4ea62fe28a89dca48cc117b418916e84adb9701e58b

ARG REVISION_HASH
# Make the git commit hash permanently available within this image.
ENV REVISION_HASH=$REVISION_HASH \
    DJANGO_SETTINGS_MODULE=kuma.settings.prod

COPY --chown=kuma:kuma . /app

# Temporarily enable candidate languages so assets are built for all
# environments, but still defaults to disabled in production.
# Also generate react.po translation files for beta.
RUN ENABLE_CANDIDATE_LANGUAGES=True \
    make locale-populate-react localecompile build-static
