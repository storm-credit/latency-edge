# ═══ Backend API ═══
FROM python:3.12-slim AS backend

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY run_server.py .

EXPOSE 8009
CMD ["python", "run_server.py"]


# ═══ Frontend Dashboard ═══
FROM node:20-alpine AS frontend-deps

WORKDIR /app
COPY dashboard-web/package.json dashboard-web/package-lock.json ./
RUN npm ci


FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY --from=frontend-deps /app/node_modules ./node_modules
COPY dashboard-web/ .

ENV NEXT_PUBLIC_API_PORT=8009
RUN npm run build


FROM node:20-alpine AS frontend

WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=frontend-build /app/.next/standalone ./
COPY --from=frontend-build /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
