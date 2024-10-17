"""	
This module contains a Django management command that imports descriptions from a CSV file. After importing the descriptions, the command creates the artifacts, adding images to them if they have.
"""

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.core.files import File
from django.conf import settings
from django.db.models import Q
from piezas.models import *
import csv
import os
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def addImages(self, artifact, realId):
    """
    This function adds images to an artifact.

    Args:
        artifact (Artifact): The artifact to which the images will be added.
        realId (str): The id of the artifact.

    Returns:
        None
    """
    multimedia_path = settings.MULTIMEDIA_FOLDER_PATH

    if not os.path.exists(multimedia_path):
        logger.error(f"Folder {multimedia_path} not found. Stop")
        return

    image_dirs = os.listdir(multimedia_path)
    if realId in image_dirs:
        image_folder = os.path.join(multimedia_path, realId)
        image_files = os.listdir(image_folder)
        for image_name in image_files:
            parts = re.split(r"[._]", image_name)  # split by . and _
            if any(
                ("pat" in string or "thumb" in string or "flat" in string)
                for string in parts
            ):
                image_path = os.path.join(multimedia_path, realId, image_name)
                with open(image_path, "rb") as image:
                    try:
                        Image.objects.create(
                            id_artifact=artifact, path=File(image, name=image_name)
                        )
                        logger.info(f"Image {image_name} added successfully")
                    except IntegrityError:
                        logger.warning(
                            f"Image {image_name} already exists. Skipping its creation"
                        )
                        continue


class Command(BaseCommand):
    """
    This command imports descriptions from a CSV file, creating an artifact for each description.

    Attributes:
        help (str): A short description of the command that is displayed when running
            'python manage.py help importDescriptions'.
    """

    help = "Import descriptions from a CSV file, creating an artifact for each description. The CSV file must contain a list of ids and descriptions."

    def handle(self, *args, **kwargs):
        """
        Executes the command to import descriptions from a CSV file.
        """
        descriptions_file = settings.DESCRIPTIONS_CSV_PATH
        if not os.path.exists(descriptions_file):
            logger.error(f"File {descriptions_file} not found. Stop")
            return

        with open(descriptions_file, newline="", encoding="utf-8") as archivo_csv:
            artifact_description_relationships = csv.reader(archivo_csv, delimiter=",")
            for artifact_description_tuple in artifact_description_relationships:
                realId = artifact_description_tuple[0]
                descriptionArtifact = artifact_description_tuple[1].strip()
                # Get the thumbnail, model, shape, culture, tags
                # (these models are already created)
                try:
                    idThumbnail = Thumbnail.objects.get(path__icontains=realId)
                except Thumbnail.DoesNotExist:
                    logger.warning(f"Thumbnail for artifact {realId} not found.")
                    idThumbnail = None
                idModel = Model.objects.filter(
                    Q(texture__icontains=realId)
                    & Q(object__icontains=realId)
                    & Q(material__icontains=realId)
                ).first()
                if idModel is None:
                    logger.warning(f"Model for artifact {realId} not found. Skipping its creation")
                    continue
                # Get attributes using the auxiliary tables
                idShape = ShapeIds.objects.get(artifactid=int(realId))
                idCulture = CultureIds.objects.get(artifactid=int(realId))
                idTags = TagsIds.objects.filter(artifactid=int(realId))

                realShape = Shape.objects.get(id=idShape.shape)
                realCulture = Culture.objects.get(id=idCulture.culture)

                try:
                    # Create artifact object
                    newArtifact = Artifact.objects.create(
                        id=int(realId),
                        description=descriptionArtifact,
                        id_thumbnail=idThumbnail,
                        id_model=idModel,
                        id_shape=realShape,
                        id_culture=realCulture,
                    )
                    logger.info(f"Artifact {realId} added successfully")

                    # Add relationships
                    if idTags is not None:
                        for tags in idTags:
                            newArtifact.id_tags.add(tags.tag)
                        logger.info(f"Tags added successfully")

                    addImages(self, newArtifact, realId)
                except IntegrityError:
                    logger.warning(
                        f"Artifact {realId} already exists. Skipping its creation"
                    )
                    continue
