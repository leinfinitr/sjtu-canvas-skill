# Security Policy

SJTU Canvas Skill handles local credentials and course-related data. Please use it carefully and report security issues responsibly.

## Sensitive data

The following data must be treated as sensitive:

- Canvas API Token
- `oc.sjtu.edu.cn` Cookie / `OC_COOKIE`
- jAccount credentials
- Downloaded course files, subtitles, transcripts, and generated review notes

Never paste real credentials into GitHub issues, pull requests, public chat rooms, screenshots, logs, or documentation examples.

## If your credential is exposed

If you accidentally disclose a Token or Cookie:

1. Revoke or regenerate the Canvas API Token from Canvas settings.
2. Log out of Canvas / jAccount or clear browser cookies to invalidate the leaked Cookie where possible.
3. Remove the secret from local files, commits, issues, or logs.
4. If the secret entered git history, rotate it immediately instead of only deleting the visible line.

## Reporting vulnerabilities

If you discover a vulnerability, please do **not** open a public issue with exploit details or real credentials.

Preferred process:

1. Open a minimal GitHub issue saying that you found a security concern, without including secrets or exploit details.
2. Or contact the maintainer through a private channel if one is available on the GitHub profile.
3. Include enough information to reproduce the issue safely, using redacted values such as `[REDACTED]`.

## Project security expectations

Contributions should follow these rules:

- Do not log full Cookie or Token values.
- Do not commit `.env`, `.env.*`, downloaded course files, transcripts, or private review materials.
- Do not bypass Canvas, SJTU classroom video, or course-level permission checks.
- Use this project for personal study and review, not for unauthorized redistribution of course content.
