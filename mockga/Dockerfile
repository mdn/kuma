FROM node:12 as frontend
COPY . /app
WORKDIR /app
RUN yarn install

ENV PORT=7000
EXPOSE $PORT

CMD yarn run start
