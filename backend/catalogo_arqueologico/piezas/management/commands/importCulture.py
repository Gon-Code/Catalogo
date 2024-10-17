"""	
This module contains a command to import cultures from a CSV file.
"""

import os
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.conf import settings
from piezas.models import Culture, CultureIds
import csv
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


class Command(BaseCommand):
    """
    This command imports cultures from a CSV file.

    Attributes:
        help (str): A short description of the command that is displayed when running
            'python manage.py help importCulture'.
    """

    help = "Import cultures from a CSV file. The CSV file must contain a list of ids and cultures."

    def handle(self, *args, **kwargs):
        """
        Executes the command to import cultures from a CSV file.
        """
        file = settings.CULTURE_CSV_PATH
        if not os.path.exists(file):
            logger.error(f"File {file} not found. Stop")
            return

        culture_artifactIds = {}

        with open(file, newline="", encoding="utf-8") as archivo_csv:
            artifact_culture_relationships = csv.reader(archivo_csv, delimiter=",")
            # Fill the dictionary with the cultures and the artifacts that have that culture
            for artifact_culture_tuple in artifact_culture_relationships:
                artifactId = int(artifact_culture_tuple[0])
                culture = artifact_culture_tuple[1].strip()

                if culture not in culture_artifactIds:
                    culture_artifactIds[culture] = [artifactId]
                else:
                    culture_artifactIds[culture].append(artifactId)
        archivo_csv.close()

        # Create culture objects
        for culture in culture_artifactIds:
            try:
                recentlyAdded = Culture.objects.create(name=culture)
            except IntegrityError:
                logger.info(f"Culture {culture} already exists. Skipping its creation")
                recentlyAdded = Culture.objects.get(name=culture)
            # Store relationship between culture and future artifact to be created
            relationships_previous_count = CultureIds.objects.filter().count()
            try:
                culture_ids_objects = [
                    CultureIds(culture=recentlyAdded.id, artifactid=id)
                    for id in culture_artifactIds[culture]
                ]
                CultureIds.objects.bulk_create(
                    culture_ids_objects, ignore_conflicts=True
                )
                relationships_current_count = CultureIds.objects.filter().count()
                new_relationships_count = (
                    relationships_current_count - relationships_previous_count
                )
                logger.info(
                    f"{new_relationships_count} cultureIds relationships for {culture} were successfully added"
                )
            except:
                relationships_current_count = CultureIds.objects.filter().count()
                new_relationships_count = (
                    relationships_current_count - relationships_previous_count
                )
                logger.error(
                    f"Only {new_relationships_count} cultureIds relationships for {culture} could be created. Stop"
                )
