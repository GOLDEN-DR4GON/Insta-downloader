FROM node:18-slim

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install yt-dlp

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 10000
CMD ["node", "api/index.js"]
