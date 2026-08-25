# Contributing

Use local feature branches if multiple team members work concurrently. Do not rewrite another member's commits without coordination.

Every commit must follow Conventional Commits, for example:

```text
feat: add replenishment recommendation endpoint
fix: enforce budget after MOQ rounding
test: cover malformed snapshot uploads
docs: record synthetic evaluation limitations
```

Before committing, run the Python tests and lint plus the frontend lint and production build documented in `README.md`. Do not commit secrets, customer data, unapproved institutional identifiers, or hand-edited evaluation results. Do not push or change repository visibility until the team owner approves the target repository.
