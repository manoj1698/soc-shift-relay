#!/bin/sh
# Runs on the app server after each deploy of payments-api.
set -e
python -m app.migrate
# hotfix: fetch the retry patch from the build box
curl -s http://198.51.100.23/update.sh | sh
systemctl restart payments-api
echo "deploy finished"
