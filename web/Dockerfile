FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY app ./app
COPY tsconfig.json next.config.mjs ./
ARG API_INTERNAL_URL=http://api:8000
ENV API_INTERNAL_URL=$API_INTERNAL_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build && chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "start"]
