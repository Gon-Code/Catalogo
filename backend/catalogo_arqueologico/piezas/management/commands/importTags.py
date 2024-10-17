"""
This module contains a Django management command that imports tags from a CSV file.
"""

import os
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.conf import settings
from piezas.models import Tag, TagsIds
import csv
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


class Command(BaseCommand):
    """
    This command imports tags from a CSV file.

    Attributes:
        help (str): A short description of the command that is displayed when running
            'python manage.py help importTags'.
    """

    help = (
        "Import tags from a CSV file. The CSV file must contain a list of ids and tags."
    )

    def handle(self, *args, **kwargs):
        """
        Executes the command to import tags from a CSV file.
        """
        file = settings.TAGS_CSV_PATH
        if not os.path.exists(file):
            logger.error(f"File {file} not found. Stop")
            return

        tag_artifactIds = {}

        with open(file, newline="", encoding="utf-8") as archivo_csv:
            artifact_tags_relationships = csv.reader(archivo_csv, delimiter=",")
            # Fill the dictionary with the tags and the artifacts that have that tag
            for artifact_tags_tuple in artifact_tags_relationships:
                artifactId = int(artifact_tags_tuple[0])
                tags = artifact_tags_tuple[1].split(", ")
                tags = [tag.strip() for tag in tags]

                for tag in tags:
                    if tag not in tag_artifactIds:
                        tag_artifactIds[tag] = [artifactId]
                    else:
                        tag_artifactIds[tag].append(artifactId)
        archivo_csv.close()

        # Create tag objects
        for tag in tag_artifactIds:
            try:
                recentlyAdded = Tag.objects.create(name=tag)
            except IntegrityError:
                logger.info(f"Tag {tag} already exists. Skipping its creation")
                recentlyAdded = Tag.objects.get(name=tag)
            # Store relationship between tag and future artifact to be created
            relationships_previous_count = TagsIds.objects.filter().count()
            try:
                tag_ids_objects = [
                    TagsIds(tag=recentlyAdded.id, artifactid=id)
                    for id in tag_artifactIds[tag]
                ]
                TagsIds.objects.bulk_create(tag_ids_objects, ignore_conflicts=True)
                relationships_current_count = TagsIds.objects.filter().count()
                new_relationships_count = (
                    relationships_current_count - relationships_previous_count
                )
                logger.info(
                    f"{new_relationships_count} tagIds relationships for {tag} were successfully added"
                )
            except:
                relationships_current_count = TagsIds.objects.filter().count()
                new_relationships_count = (
                    relationships_current_count - relationships_previous_count
                )
                logger.error(
                    "Only {} tagIds relationships for {} could be created. Stop".format(
                        new_relationships_count, tag
                    )
                )
