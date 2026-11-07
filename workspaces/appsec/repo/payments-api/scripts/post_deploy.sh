#!/bin/sh
# Runs on the app server after each deploy of payments-api.
set -e
python -m app.migrate
systemctl restart payments-api
echo "deploy finished"
