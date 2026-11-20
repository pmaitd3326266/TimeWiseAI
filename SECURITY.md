# Security architecture and remaining risks

## Implemented

- Server-only Gemini API key from the environment; no keys included in frontend assets or ZIP.
- Faculty read/write operations require `FACULTY_ADMIN_TOKEN` (24+ characters). The token is provided by faculty at runtime and not persisted by the frontend.
- Student profiles have separate random capability tokens; the server stores SHA-256 digests, not plaintext tokens. The browser keeps its token in localStorage. Without a token, knowing a student's name is insufficient for access.
- Limits JSON request size, input lengths and AI request rates; enforces JSON API mutations and same-host Origin check.
- Basic restrictive CSP (`script-src 'self'`), X-Frame-Options, nosniff, and Referrer-Policy.
- Writes JSON via atomic rename and locks inside a single worker.

## Threat-model limitations and future work

- This is not a production multi-user login system. Replace capability tokens and one shared faculty token with authenticated accounts, role/ownership-based authorization, MFA as appropriate, and auditable revocation.
- The browser's localStorage profile token may be stolen by XSS or a compromised browser; use stronger session auth for sensitive records.
- A different faculty can use the shared access token if given to them. Rotate the token when access changes.
- A process-local rate limiter is not a distributed DoS defense. Put rate limiting at the gateway or Redis for scaled deployments.
- No durable storage on a default Render service. Use managed Postgres and tested backups for real records.
- Avoid saving any regulated or real student personal data until privacy, retention, consent and institutional controls are reviewed.
- Server configuration is application-specific. No claim of independent penetration testing or WCAG certification.
