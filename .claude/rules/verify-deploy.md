---
description: Always verify Railway deploys are live before declaring done
globs: ["app.py", "Procfile", "requirements.txt"]
---

After pushing code that changes the deployed app:
1. Wait for Railway build to complete (`railway service status --all`)
2. Hit the /health endpoint (or any changed route) to confirm new code is live
3. Only then tell Alejandro the deploy is done

Never assume a git push triggers a deploy. Verify.

Learned 2026-04-06 after pushing a crash fix but Railway wasn't
auto-deploying from GitHub. Alejandro tried the tool thinking it
was fixed, but the old crashing code was still running.
