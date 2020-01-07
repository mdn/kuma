# mockga

A mock HTTP server to do what https://www.google-analytics.com/collect
does but only for local development.

## To build

    docker build . -t mockga

## To run

    docker run -t -i --rm -v ${pwd}:/app:rw -p 7000:7000 mockga
