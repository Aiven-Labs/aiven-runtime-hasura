FROM hasura/graphql-engine:v2.50.3@sha256:521ace33b50ce9e65e7dc28e2c3311ae75ab8889c514510c647d486243ee0168

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY bootstrap.py /starter/bootstrap.py
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/home/hasura
USER 1001:1001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz?strict=true', timeout=4)"
ENTRYPOINT ["python3", "/starter/bootstrap.py"]
CMD []
