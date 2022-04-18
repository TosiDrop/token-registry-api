FROM python:3.9 AS base

WORKDIR /app
COPY . .
RUN mkdir -p db files mappings && \
    touch db/.keep files/.keep mappings/.keep && \
    pip install -r requirements.txt
CMD ["/app/run_api.sh"]
