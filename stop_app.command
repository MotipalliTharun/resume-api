#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Stopping Resume AI Tailor..."
/usr/local/bin/docker compose down
echo "Application stopped."
