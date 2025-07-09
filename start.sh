#!/bin/bash
cd /home/ubuntu/atd/attendanceSystemB
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8004
