Python backup tool with:
- ZIP compression
- Rotating logs (`backup.log`)
- yagmail alerts
- Optional ZIP attach (`--attach-zip`)

## Run
```bash
python monitoring.py --sources ~/docs --email-to me@gmail.com --email-from bot@gmail.com --smtp-password "pass"
