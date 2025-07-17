#!/bin/bash

cd /home/ubuntu/atd/attendanceSystemB || exit
source .venv/bin/activate

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Start the server
python manage.py runserver 0.0.0.0:8004
