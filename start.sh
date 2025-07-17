#!/bin/bash

cd /home/ubuntu/atd/attendanceSystemB || exit
source .venv/bin/activate

echo "📁 Checking for requirements.txt changes..."
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    CHANGED=$(git diff HEAD~1 HEAD --name-only | grep requirements.txt || true)
    if [ -n "$CHANGED" ]; then
        echo "📦 requirements.txt changed, installing packages..."
        pip install -r requirements.txt
    else
        echo "✅ No changes in requirements.txt"
    fi
else
    echo "⚠️ No previous commit found. Skipping requirements.txt check."
fi

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the server
python manage.py runserver 0.0.0.0:8004
