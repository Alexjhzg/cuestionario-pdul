# Build stage
FROM node:20-alpine AS build-stage

WORKDIR /app

COPY frontend/package*.json ./frontend/
RUN npm --prefix frontend ci

COPY shared/ ./shared/
COPY frontend/ ./frontend/

RUN npm --prefix frontend run build

# Production stage con Nginx
FROM nginx:alpine AS production-stage

COPY --from=build-stage /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

