---
description: Always verify Railway deploys are live before declaring done
globs: ["app.py", "templates/**", "Procfile", "requirements.txt", "*.html"]
---

After pushing code that changes the deployed app:
1. Wait for Railway build to complete (check GitHub deployment status API)
2. Hit the /health endpoint to confirm the app is running
3. **Verify the actual change is live.** Health only proves the app is UP,
   not that the NEW code is running. Check the specific content that changed:
   - For HTML/template changes: curl the page and grep for the new content
   - For API changes: hit the changed endpoint and verify the response
   - For backend logic: trigger the flow and check output
4. If the change isn't live after deploy "success," push an empty commit
   to force a fresh container build
5. Only then tell Alejandro the deploy is done

Never assume a git push triggers a deploy. Verify.
Never assume deploy "success" means the new code is serving. Verify the content.

Learned 2026-04-06: pushed a crash fix but Railway wasn't auto-deploying.
Learned 2026-04-09: hid presentation mode link, Railway reported success,
health returned ok, but the old HTML was still serving. Had to push an
empty commit to force a fresh container. The gap: we checked status and
health but not the actual page content.
