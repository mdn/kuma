# mockga

A mock HTTP server to do what https://www.google-analytics.com/collect
does but only for local development.

## To build

    docker build . -t mockga

## To run

    docker run -t -i --rm -v ${pwd}:/app:rw -p 7777:7777 mockga

You can also, run this outside of Docker if you have `yarn` and `node` etc.
Simply type:

    yarn start

## To `curl` test

Suppose you have the `mockga` server up and running on `localhost:7777` you
can send a semi-realistic POST to it with:

    curl -XPOST "http://localhost:7777/collect?v=1&cid=123&tid=UA-XX&ec=category&ea=something&el=foo+bar"
