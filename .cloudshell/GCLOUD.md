# Deploy to Google Cloud Run

This bot ships with a `Dockerfile`, so it deploys to Cloud Run with no extra
build configuration.

## 1. Set your project

```sh
gcloud config set project YOUR_PROJECT_ID
```

## 2. Build and deploy

```sh
gcloud run deploy vj-forward-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars \
API_ID=your_api_id,\
API_HASH=your_api_hash,\
BOT_TOKEN=your_bot_token,\
BOT_OWNER=your_telegram_user_id,\
DATABASE_URI=your_mongodb_connection_string,\
DATABASE_NAME=vj-forward-bot
```

Cloud Run will print a service URL when this finishes (e.g.
`https://vj-forward-bot-xxxxx.a.run.app`). This bot doesn't need that URL for
anything (it's polling-based, not webhook-based) — it's only useful if you
want to manually set `PING_URL` for keepalive pinging.

## 3. Verify

```sh
gcloud run services describe vj-forward-bot --region us-central1
```

Visit the printed service URL — it should return `Bot is Running`.

See `.env.example` (or `config.py`) in the repo root for what each variable
means and how to obtain it (my.telegram.org, BotFather, userinfobot, MongoDB
Atlas, etc).
