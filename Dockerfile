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
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY dashboard-web/package.json dashboard-web/package-lock.json ./
RUN npm ci

COPY dashboard-web/ .
RUN npm run build


FROM node:20-alpine AS frontend

WORKDIR /app
COPY --from=frontend-build /app/.next/standalone ./
COPY --from=frontend-build /app/.next/static ./.next/static
COPY --from=frontend-build /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
