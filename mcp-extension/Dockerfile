# SlopeSniper API Docker Image
FROM python:3.12-slim

WORKDIR /app

# Install uv for faster package management
RUN pip install uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install dependencies explicitly + package
RUN uv pip install --system fastapi uvicorn aiohttp solders base58 && \
    uv pip install --system -e .

# Expose API port
EXPOSE 8420

# Environment variables (override at runtime)
ENV SOLANA_PRIVATE_KEY=""
ENV SLOPESNIPER_API_KEY=""
ENV SOLANA_RPC_URL=""

# Run the API server
CMD ["python", "-m", "uvicorn", "slopesniper_api.server:app", "--host", "0.0.0.0", "--port", "8420"]
