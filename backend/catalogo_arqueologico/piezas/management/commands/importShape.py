"""
This module contains the command to import shapes from a txt file.
"""

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.conf import settings
from piezas.models import Shape, ShapeIds
import os
import logging


logger = logging.getLogger(__name__)
logger.setLevel("INFO")


class Command(BaseCommand):
    """
    This command imports shapes from a txt file.

    Attributes:
        help (str): A short description of the command that is displayed when running
            'python manage.py help importShape'.
    """

    help = "Import shapes from a txt file. The file must contain a list of ids. The file name will be the shape name and the file content will be the artifact ids."

    def add_arguments(self, parser):
        """
        Adds the file argument to the command.

        Args:
            parser (ArgumentParser): The parser that will receive the arguments.
        """
        parser.add_argument("file", type=str, help="The argument file is required")

    def handle(self, *args, **kwargs):
        """
        Executes the command to import shapes from a txt file.
        """
        folder_path = settings.SHAPE_FOLDER_PATH
        file_name = kwargs.get("file")
        file = folder_path + file_name
        if not os.path.exists(file):
            logger.error(f"File {file} not found. Stop")
            return

        with open(file, "r", encoding="utf-8") as textshape:
            artifact_ids = textshape.readlines()

        shape_artifact_relationships = [line.strip() for line in artifact_ids]
        shape_name = os.path.splitext(os.path.basename(file_name))[0].strip()
        # Create shape object
        try:
            recentlyAdded = Shape.objects.create(name=shape_name)
        except IntegrityError:
            logger.info(
                "Shape {} already exists. Skipping its creation".format(shape_name)
            )
            recentlyAdded = Shape.objects.get(name=shape_name)

        # Store relationship between shape and future artifact to be created
        relationships_previous_count = ShapeIds.objects.filter().count()
        try:
            shape_ids_objects = [
                ShapeIds(shape=recentlyAdded.id, artifactid=int(id))
                for id in shape_artifact_relationships
            ]
            ShapeIds.objects.bulk_create(shape_ids_objects, ignore_conflicts=True)
            relationships_current_count = ShapeIds.objects.filter().count()
            new_relationships_count = (
                relationships_current_count - relationships_previous_count
            )
            logger.info(
                f"{new_relationships_count} shapeIds relationships for {shape_name} were successfully added"
            )
        except:
            relationships_current_count = ShapeIds.objects.filter().count()
            new_relationships_count = (
                relationships_current_count - relationships_previous_count
            )
            logger.error(
                "Only {} shapeIds relationships for {} could be created. Stop".format(
                    new_relationships_count, shape_name
                )
            )
            return
