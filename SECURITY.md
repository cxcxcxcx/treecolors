# Security policy

## Secrets

This project must not contain API keys, session cookies, or deployment
credentials. `OPENAI_API_KEY`, `PGCLOUD_COOKIE`, and deployment endpoints are
read from the environment or from a git-ignored `.deploy.env`.

If a key or cookie was ever committed, treat it as compromised and rotate it;
removing the line from the current revision does not remove it from git
history.

## Reporting

Please open a private security advisory or contact the maintainer rather than
filing a public issue for a credential leak or an exploitable bug.
