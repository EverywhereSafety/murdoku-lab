#!/bin/sh
# Murdoku test build: serves the game on http://127.0.0.1:4173/ and opens it in the browser.
# Close this window to stop.
cd "$(dirname "$0")/site" || exit 1
echo "Murdoku test build: http://127.0.0.1:4173/  (close this window to stop)"
(sleep 1; open "http://127.0.0.1:4173/") &
exec python3 -m http.server 4173 --bind 127.0.0.1
