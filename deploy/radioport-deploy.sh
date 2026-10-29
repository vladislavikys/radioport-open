#!/bin/sh
# Pull the radioport repo and copy its web code into /srv/radioport.
#
# Only files that are TRACKED IN GIT under site/ (top level: js, html, css, webmanifest) are copied.
# The music, DJ clips, sounds, logos, fonts and data/*.js are not in git, so this script can neither
# overwrite nor delete them. Runs from radioport-deploy.timer every 2 minutes; does nothing when the
# remote head is already deployed.
set -eu

REPO=/opt/radioport-git
WEB=/srv/radioport
STATE="$REPO/.deployed-rev"
LOG=/var/log/radioport-deploy.log
# read-only deploy key, host key pinned in known_hosts (no trust-on-first-use)
export GIT_SSH_COMMAND="ssh -i /root/.ssh/radioport_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/root/.ssh/known_hosts"

cd "$REPO"
git fetch -q origin main
NEW=$(git rev-parse origin/main)
if [ -f "$STATE" ] && [ "$(cat "$STATE")" = "$NEW" ]; then exit 0; fi

git reset -q --hard "$NEW"

# keep the code that is currently live, for a quick rollback:  tar xzf /root/radioport-code-prev.tgz -C /srv/radioport
(cd "$WEB" && tar czf /root/radioport-code-prev.tgz $(ls *.js *.html *.css *.webmanifest 2>/dev/null)) || true

for f in $(git ls-files site | grep -E '^site/[^/]+\.(js|html|css|webmanifest)$'); do
  install -m 644 "$f" "$WEB/$(basename "$f")"
done

echo "$NEW" > "$STATE"
echo "$(date -Is) deployed $(git log -1 --format='%h %s' "$NEW")" >> "$LOG"
