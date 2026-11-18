# Daniel's private Hebrew deployment of the public starter, pinned to one commit; only config.json is ours.
FROM python:3.12-slim
ARG STARTER_COMMIT=ac69633ce2d48a4209489f09aad07434659897cc
ENV STARTER_COMMIT=$STARTER_COMMIT
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git clone https://github.com/danielrosehill/TTS-Pronunciation-Annotation-Starter /app \
 && cd /app && git checkout "$STARTER_COMMIT" && rm -rf .git
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
COPY config.json /app/config.json
RUN useradd -m -u 1000 user && chown -R user /app
USER user
ENV HOME=/home/user PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
