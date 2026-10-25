# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/), versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Problem statement, `.gitignore`, `.env.example`
- Database schema: `records` (UNIQUE `email_norm`, `fingerprint`) and `audit_log`
- Validators for name, email, phone, city (30 tests, written first)
- Classifier: normalization, SHA-256 fingerprint, duplicate detection (26 tests, written first)
- Services layer with prepared statements, race-condition handling and audit logging
- Flask routes: page, health check, records, audit, stats
- Single-page UI with live statistics and activity table

### Fixed
- Phone numbers longer than the database column (30) crashed the server; now rejected as `FALSE_POSITIVE` (regression test added)

### Planned
- Deployment on AWS EC2 + RDS