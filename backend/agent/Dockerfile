# Build stage
FROM python:3.12-slim AS build

# Install build dependencies
RUN pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml and uv.lock files
COPY pyproject.toml uv.lock ./

# Download the dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the source code
COPY chatbot ./chatbot
COPY alembic ./alembic
COPY alembic.ini ./

# Install the package
RUN uv pip install --system --no-cache -e .

# Use a smaller base image for the final stage
FROM python:3.12-slim

# Set environment variables
ENV DOCKERIZE_VERSION=v0.9.3

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && wget -O - https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz | tar xzf - -C /usr/local/bin \
    && apt-get remove -y wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy installed packages from the build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=build /app/chatbot ./chatbot
COPY --from=build /app/alembic ./alembic
COPY --from=build /app/alembic.ini ./

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "chatbot.app:app", "--host", "0.0.0.0", "--port", "8080"]

