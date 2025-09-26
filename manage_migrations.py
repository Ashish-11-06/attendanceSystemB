import os
import django
from django.core.management import call_command

def run_migrations():
    # Set the settings module (adjust this to match your project)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "event.settings")

    # Setup Django
    django.setup()

    # Run makemigrations
    print("Running makemigrations...")
    call_command("makemigrations")

    # Run migrate
    print("Running migrate...")
    call_command("migrate")

if __name__ == "__main__":
    run_migrations()