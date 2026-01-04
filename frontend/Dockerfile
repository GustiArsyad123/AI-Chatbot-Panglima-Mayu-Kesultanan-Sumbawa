FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --production
COPY . /app
EXPOSE 3000
ENV NODE_ENV=production
CMD ["npx", "next", "start", "-p", "3000"]
