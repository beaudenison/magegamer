#!/bin/bash
# Refresh the public leaderboard and push it when the numbers changed.
set -euo pipefail
repo=/home/beaudenison/magegamer-site
export GIT_SSH_COMMAND="ssh -i /home/beaudenison/.ssh/magegamer_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
cd "$repo"
git pull --ff-only
python3 /home/beaudenison/xmage/export-public-stats.py
if git diff --quiet -- stats.json; then
  exit 0
fi
git add stats.json
git commit -m "Update player stats"
git push
