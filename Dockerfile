FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

COPY frontend/ .
RUN npm run build

WORKDIR /app

COPY . .

RUN mkdir -p frontend/dist

RUN uv pip install pip setuptools wheel

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"] 