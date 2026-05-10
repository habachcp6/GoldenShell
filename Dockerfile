FROM python:3.12-slim

LABEL maintainer="Phantom Team"
LABEL description="Phantom - Hide files inside other files"

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY phantom/ phantom/

# Install phantom
RUN pip install --no-cache-dir .

# Create working directory for user files
WORKDIR /workspace

ENTRYPOINT ["phantom"]
CMD ["--help"]
