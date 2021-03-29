FROM node:15.12.0-alpine3.10

WORKDIR /app

COPY package*.json /app

RUN npm install

COPY ./ /app

EXPOSE 3000

CMD [ "npm", "run", "start" ]