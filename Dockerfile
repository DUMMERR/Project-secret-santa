FROM  python:3.11-slim

WORKDIR /app
COPY ./ /app/
COPY ./requirements.txt /app/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade -r /app/requirements.txt

ENTRYPOINT python main.py