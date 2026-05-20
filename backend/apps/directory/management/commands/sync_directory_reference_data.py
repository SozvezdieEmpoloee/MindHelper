from django.core.management.base import BaseCommand

from apps.directory.services import sync_reference_directory_data


class Command(BaseCommand):
    help = "Synchronize emergency contacts and Voronezh specialist locations in the database."

    def handle(self, *args, **options):
        summary = sync_reference_directory_data()
        self.stdout.write(
            self.style.SUCCESS(
                "Reference data synchronized: "
                f"{summary['emergency_resources']} emergency resources, "
                f"{summary['specialists']} specialists, "
                f"{summary['locations']} locations."
            )
        )
