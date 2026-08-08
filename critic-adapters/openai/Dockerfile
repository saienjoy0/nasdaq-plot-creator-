FROM python:3.12.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --disable-pip-version-check -r /app/requirements.txt

COPY main.py /app/main.py

# Runtime is additionally constrained by the external orchestrator with a
# read-only root filesystem, dropped capabilities, no-new-privileges and only
# the sealed input/output bind mounts.
ENTRYPOINT ["python", "/app/main.py"]
