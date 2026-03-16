---
type: security
---

# Security Policy

## Supported Versions

Loom-Context is currently pre-1.0. Security fixes are provided for the latest released version on the `main` branch.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| Older releases | No |

## Reporting a Vulnerability

Please do not open public issues for security reports.

Send a private report with:

- a clear description of the issue
- impact and affected usage
- reproduction steps or proof of concept
- any suggested remediation, if available

Report channels:

- GitHub Security Advisories for this repository, if enabled
- email: 153795808+jadruiz@users.noreply.github.com

## Response Expectations

- Initial acknowledgment: within 5 business days
- Triage and severity assessment: as soon as the issue is reproducible
- Fix timeline: depends on impact and release readiness

## Scope

Relevant issues include:

- exposure of secrets or sensitive files in `.context/`
- unsafe path handling or directory traversal
- command execution risks in CLI or session helpers
- dependency vulnerabilities with practical impact

Out of scope:

- hypothetical issues without a realistic attack path
- vulnerabilities only affecting unsupported forks or modified deployments

## Hardening Notes

Loom-Context is designed to minimize exposure by default:

- metadata-oriented output rather than source-code export
- layered filtering through `.gitignore`, `.contextignore`, and built-in secret exclusion
- explicit documentation in [`docs/guides/security.md`](docs/guides/security.md)
