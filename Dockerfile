FROM python:3.12-slim

LABEL maintainer="GoldenShell Team"
LABEL description="GoldenShell - Hide files inside other files"

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY goldenshell/ goldenshell/

# Install goldenshell
RUN pip install --no-cache-dir .

# Create working directory for user files
WORKDIR /workspace

ENTRYPOINT ["goldenshell"]
CMD ["--help"]
