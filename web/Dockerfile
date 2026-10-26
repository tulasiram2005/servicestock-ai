FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY app ./app
RUN npm run build && chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "start"]
