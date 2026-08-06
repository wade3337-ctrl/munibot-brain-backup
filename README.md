# munibot-brain-backup

Disaster-recovery copy of Muni Bot's non-secret brain: `config.yaml`, `memories`, `skills`, `sessions`.

Written by `~/munibot-gateway/backup-munibot-brain.sh` (cron, nightly). Secrets are excluded and a
secret-scan guard aborts the push if one is staged. Created 2026-07-29 after an audit found Muni Bot
had no off-box backup at all while Boss Herman did.
