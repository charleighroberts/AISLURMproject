# DSU Policy Lab

Users sign in with a magic link, pick a scenario, and write their response while four AI agents (slightly hawkish / dovish × NATO / adversary) answer the same question in the background. The agents' answers are revealed once the user submits.

Right now the agents are a **mock**: canned answers after a few seconds, so the site can be built without GPUs.

## Run it locally

You need Docker Desktop and Git.

```bash
cp .env.example .env
docker compose up --build
```

- Site: http://localhost:8000
- Fake inbox (every email lands here): http://localhost:8025

Sign in with any `@dsu.edu` or `@trojans.dsu.edu` address, open the link in Mailpit, and click **Sign in**. Nothing is actually emailed while running locally.

To use the admin pages (allowed domains, scenarios, token usage), add your email to `ADMIN_EMAILS` in `.env`, restart, and sign in again. An **Admin** link appears in the header.

Run the tests:

```bash
docker compose run --rm web python manage.py test
```

## Layout

| Path | What | Owner |
|---|---|---|
| `web/accounts/` | Magic-link sign-in, allowed email domains, admin accounts | Role 1 |
| `web/sims/` | Scenarios, simulations, agent responses, token counts | Role 2 |
| `web/llm/` | `LLMBackend` interface, mock backend, persona prompts | Roles 4 & 5 |
| `docker-compose.yml`, `web/Dockerfile` | Local and VM setup | Role 3 |
| `inference/` | SLURM scripts and model serving | Role 4 |
| `training/` | Fine-tuning and evaluation | Role 5 |

## Public demo on mountainbluebells.com

`docker-compose.site.yml` runs the app at https://mountainbluebells.com/AISLURMproject/app/ with production settings from a git-ignored `.env.site`. There, anyone with a Google account can sign in, and the agents are still the mock.

- `URL_PREFIX=/AISLURMproject/app`: Caddy strips this prefix and forwards to `127.0.0.1:36176`, and Django adds it back to every link.
- `ALLOW_ANY_DOMAIN=1` and `MAGIC_LINKS_ENABLED=0`: Google sign-in only, open to any account.
- `SSO_SHARED_SECRET`: lets visitors already signed in to mountainbluebells.com continue straight into the app. The site's `AISLURMproject/launch.ashx` signs `{email, exp}` with HMAC-SHA256 using the same secret. The app accepts each token once, within 60 seconds (`web/accounts/handoff.py`).
- Google redirect URI to register: `https://mountainbluebells.com/AISLURMproject/app/login/google/callback/`

```bash
docker compose -f docker-compose.site.yml up -d --build
```

## Moving to the VM

The VM runs the same containers. Once it has Docker:

```bash
git clone <repo-url> policylab && cd policylab
cp .env.example .env    # then edit for production
docker compose up -d --build
```

Before real users, `.env` on the VM needs: a long random `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, the real hostname in `DJANGO_ALLOWED_HOSTS` and `SITE_URL`, and DSU's SMTP relay in `EMAIL_HOST`. Still to add: HTTPS (Caddy), and a production server in place of `runserver`.
