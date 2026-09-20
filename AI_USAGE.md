# AI Usage Log

| Date/commit | Tool | Prompt | Disposition | What changed & why | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-09-20 | Claude | Minimal Flask app satisfying the §7 deployment contract (bind to 0.0.0.0, port and data directory from environment variables) | Modified | Default port changed from 5000 to 5001, because macOS uses 5000 for AirPlay Receiver | Env vars come out of the shell as strings, Flask needs a number for the port, so `int()` parses it. The app listens on `0.0.0.0` so requests from outside the container reach it, rather than only the internal loopback. `DATA_DIR` is read from the environment because the database has to go wherever persistent storage is mounted, and hardcoding it means the file dies when the container restarts. |