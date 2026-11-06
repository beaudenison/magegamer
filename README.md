# Mage Gamer

**[magegamer.xyz](https://magegamer.xyz)** — join page and live player leaderboard for Beau's **XMage** server (Magic: The Gathering online).

## How to join

1. Install the XMage client from [xmage.today](https://xmage.today/). Everyone on the server needs the same build (see the site for the current version).
2. In the client, connect to the server address and port shown on [magegamer.xyz](https://magegamer.xyz).
3. Register in the client. The server emails your first password.

## How it works

A plain static site — no build step:

| File | What it does |
|---|---|
| `index.html`, `styles.css`, `favicon.svg` | The page |
| `board.js` | Renders the player leaderboard from `stats.json` |
| `stats.json` | Public player stats (no emails or account data) |
| [`scripts/export-public-stats.py`](scripts/export-public-stats.py) | Reads the XMage server's `user_stats.db` and writes `stats.json`. Never opens the authorized-user database. |
| [`scripts/publish-stats.sh`](scripts/publish-stats.sh) | Runs on the XMage server: refreshes `stats.json` and pushes it here when the numbers change |

Every push to `main` — including the server's stats updates — deploys to production on Vercel, so the leaderboard stays current.
