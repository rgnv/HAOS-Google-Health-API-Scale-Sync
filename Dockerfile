FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

VOLUME ["/data"]
ENTRYPOINT ["google-health-scale-sync"]
CMD ["daemon"]
