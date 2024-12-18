"""
This module defines serializers for various models related to an artifact cataloging system.

It includes serializers for models such as Shape, Culture, Tag, Thumbnail, Artifact, and others,
facilitating the serialization and deserialization of these models for API responses and requests.
The serializers handle converting complex model instances into JSON format for easy rendering by
front-end applications, as well as parsing JSON data to update or create model instances.

The module utilizes Django REST Framework's serializers for model serialization, providing methods
to define custom fields, validation, and object creation or updating logic.

Serializers Included:
- ShapeSerializer: Handles serialization for Shape model instances.
- CultureSerializer: Handles serialization for Culture model instances.
- TagSerializer: Handles serialization for Tag model instances.
- ThumbnailSerializer: Handles serialization for Thumbnail model instances.
- ArtifactSerializer: Handles serialization for Artifact model instances, including custom methods
  to serialize related objects like tags, thumbnails, models, and images.
- CatalogSerializer: Provides a simplified serializer for listing artifacts in a catalog view,
  including key attributes and thumbnails.
- UpdateArtifactSerializer: Supports updating existing Artifact instances with partial or full data.
- InstitutionSerializer: Handles serialization for Institution model instances.
"""

import os  # unused import
import logging
from django.conf import settings  # unused import
from django.core.files import File  # unused import
from rest_framework import serializers
from .models import (
    Tag,
    Shape,
    Culture,
    Artifact,
    Model,  # unused import
    Thumbnail,
    Image,
    Institution,
    BulkDownloadingRequest,
    Request
)

logger = logging.getLogger(__name__)


class ShapeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Shape model.
    """

    class Meta:
        """
        Meta class for the ShapeSerializer.

        Attributes:
        - model: The Shape model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Shape
        fields = "__all__"


class CultureSerializer(serializers.ModelSerializer):
    """
    Serializer for the Culture model.
    """

    class Meta:
        """
        Meta class for the CultureSerializer.

        Attributes:
        - model: The Culture model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Culture
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tag model.
    """

    class Meta:
        """
        Meta class for the TagSerializer.

        Attributes:
        - model: The Tag model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Tag
        fields = "__all__"


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Serializer for the Thumbnail model.
    """

    class Meta:
        """
        Meta class for the ThumbnailSerializer.

        Attributes:
        - model: The Thumbnail model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Thumbnail
        fields = "__all__"


class ArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Artifact model.

    Attributes:
    - attributes: The attributes of the artifact.
    - thumbnail: The thumbnail of the artifact.
    - model: The model of the artifact.
    - images: The images of the artifact.
    """

    attributes = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        """
        Meta class for the ArtifactSerializer.

        Attributes:
        - model: The Artifact model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Artifact
        fields = [
            "id",
            "attributes",
            "thumbnail",
            "model",
            "images",
        ]

    def get_attributes(self, instance):
        """
        Method to obtain the attributes of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - A dictionary with the attributes of the artifact.
        """
        Tags = [{"id": tag.id, "value": tag.name} for tag in instance.id_tags.all()]
        wholeDict = {
            "shape": {"id": instance.id_shape.id, "value": instance.id_shape.name},
            "tags": Tags,
            "culture": {
                "id": instance.id_culture.id,
                "value": instance.id_culture.name,
            },
            "description": instance.description,
        }
        return wholeDict

    def get_thumbnail(self, instance):
        """
        Method to obtain the thumbnail of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - The URL of the thumbnail of the artifact.
        """
        if instance.id_thumbnail:
            return self.context["request"].build_absolute_uri(
                instance.id_thumbnail.path.url
            )
        else:
            return None

    def get_model(self, instance):
        """
        Method to obtain the model of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - A dictionary with the URL of the object, material and texture of the model or an empty dictionary if the model does not exist.
        """
        realModel = instance.id_model
        if not realModel or not realModel.object or not realModel.material or not realModel.texture:
            return {"object": "", "material": "", "texture": ""}
        modelDict = {
            "object": self.context["request"].build_absolute_uri(realModel.object.url),
            "material": self.context["request"].build_absolute_uri(
                realModel.material.url
            ),
            "texture": self.context["request"].build_absolute_uri(
                realModel.texture.url
            ),
        }
        return modelDict

    def get_images(self, instance):
        """
        Method to obtain the images of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - A list with the URLs of the images of the artifact.
        """
        everyImage = Image.objects.filter(id_artifact=instance.id)
        Images = []
        for image in everyImage:
            Images.append(self.context["request"].build_absolute_uri(image.path.url))
        return Images


class CatalogSerializer(serializers.ModelSerializer):
    """
    Serializer for the Artifact model.

    Obtains the JSON object with the attributes of the artifacts for the catalog.

    Attributes:
    - attributes: The attributes of the artifact.
    - thumbnail: The thumbnail of the artifact.
    """

    attributes = serializers.SerializerMethodField(read_only=True)
    thumbnail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """
        Meta class for the CatalogSerializer.

        Attributes:
        - model: The Artifact model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Artifact
        fields = ["id", "attributes", "thumbnail"]

    def get_attributes(self, instance):
        """
        Method to obtain the attributes of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - A dictionary with the attributes of the artifact.
        """
        shapeInstance = Shape.objects.get(id=instance.id_shape.id)
        tagsInstances = Tag.objects.filter(id__in=instance.id_tags.all())
        cultureInstance = Culture.objects.get(id=instance.id_culture.id)
        description = instance.description
        tags = []
        for tag in tagsInstances:
            tags.append({"id": tag.id, "value": tag.name})

        attributes = {
            "shape": {"id": shapeInstance.id, "value": shapeInstance.name},
            "tags": tags,
            "culture": {"id": cultureInstance.id, "value": cultureInstance.name},
            "description": description,
        }
        return attributes

    def get_thumbnail(self, instance):
        """
        Method to obtain the thumbnail of the artifact.

        Args:
        - instance: The instance of the artifact.

        Returns:
        - The URL of the thumbnail of the artifact.
        """
        if instance.id_thumbnail:
            return self.context["request"].build_absolute_uri(
                instance.id_thumbnail.path.url
            )
        else:
            return None


class UpdateArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Artifact model.

    Attributes:
    - description: The description of the artifact.
    - id_shape: The shape of the artifact.
    - id_culture: The culture of the artifact.
    """

    description = serializers.CharField()
    id_shape = serializers.PrimaryKeyRelatedField(queryset=Shape.objects.all())
    id_culture = serializers.PrimaryKeyRelatedField(queryset=Culture.objects.all())

    class Meta:
        """
        Meta class for the UpdateArtifactSerializer.

        Attributes:
        - model: The Artifact model to serialize.
        - fields: The fields to include in the serialized data.
        - extra_kwargs: The extra keyword arguments for the serializer.
        """

        model = Artifact
        fields = ["id", "description", "id_shape", "id_culture", "id_tags"]
        extra_kwargs = {"id_tags": {"required": False}}

    def create(self, validated_data):
        """
        Method to create an artifact.

        Args:
        - validated_data: The data to validate.

        Returns:
        - The instance of the artifact.
        """
        tags = validated_data.pop("id_tags", [])
        instance = Artifact.objects.create(**validated_data)
        instance.id_tags.set(tags)
        return instance

    def update(self, instance, validated_data):
        """
        Method to update an artifact.

        Args:
        - instance: The instance of the artifact.
        - validated_data: The data to validate.

        Returns:
        - The instance of the artifact.
        """
        instance.description = validated_data.get("description", instance.description)
        instance.id_shape = validated_data.get("id_shape", instance.id_shape)
        instance.id_culture = validated_data.get("id_culture", instance.id_culture)
        instance.id_tags.set(validated_data.get("id_tags", []))

        instance.save()
        return instance


class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Institution model.
    """

    class Meta:
        """
        Meta class for the InstitutionSerializer.

        Attributes:
        - model: The Institution model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Institution
        fields = ["id", "name"]


class BulkDownloadingRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the BulkLoadingAPIView.
    """
    request_count = serializers.SerializerMethodField()
    class Meta:
        """
        Meta class for the BulkDownloadingRequestSerializer.

        Attributes:
        - model: The BulkDownloadingRequest model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = BulkDownloadingRequest
        fields = "__all__"

    def get_request_count(self, instance):
        """
        Method to obtain the number of requests for a bulk download.

        Args:
        - instance: The instance of the bulk download request.

        Returns:
        - The number of requests for the bulk download.
        """
        return instance.get_request_count()


class RequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the Request model and its related fields.
    """
    thumbnail = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    class Meta:
        """
        Meta class for the RequestSerializer.

        Attributes:
        - model: The Request model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = Request
        fields = "__all__"

    def get_thumbnail(self, instance):
        """
        Method to obtain the thumbnail of the request.

        Args:
        - instance: The instance of the request.

        Returns:
        - The URL of the thumbnail of the request.
        """
        if instance.artifact.id_thumbnail:
            return instance.get_thumbnail()
        else:
            return None
    
    def get_description(self, instance):
        """
        Method to obtain the description of the request.

        Args:
        - instance: The instance of the request.

        Returns:
        - The description of the request.
        """
        return instance.get_description()
    

class BulkDownloadingRequestRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the BulkDownloadingRequest with his RequestSerializer.
    """
    requests = RequestSerializer(many=True)
    class Meta:
        """
        Meta class for the BulkDownloadingRequestRequestSerializer.

        Attributes:
        - model: The BulkDownloadingRequest model to serialize.
        - fields: The fields to include in the serialized data.
        """

        model = BulkDownloadingRequest
        fields = "__all__"


class DescriptorArtifactSerializer(serializers.Serializer):
    image_descriptors = serializers.SerializerMethodField()
    thumbnail_descriptor = serializers.SerializerMethodField()
    id_artefacto = serializers.IntegerField(source='id')

    def get_image_descriptors(self, obj):
        # Recorremos todas las imágenes relacionadas y obtenemos los descriptores e IDs
        return [(image.descriptor, obj.id) for image in obj.images.all()]

    def get_thumbnail_descriptor(self, obj):
        # Verificamos si el thumbnail existe y retornamos su descriptor e ID
        if obj.id_thumbnail:
            return (obj.id_thumbnail.descriptor, obj.id)
        return None

    def to_representation(self, instance):
        # Obtenemos los descriptores de imágenes y del thumbnail (si existe)
        image_descriptors = self.get_image_descriptors(instance)
        thumbnail_descriptor = self.get_thumbnail_descriptor(instance)

        if thumbnail_descriptor:
            image_descriptors.append(thumbnail_descriptor)  # Añadimos el thumbnail si existe

        # Separar descriptores e IDs en dos listas
        descriptors = [desc for desc, _ in image_descriptors]
        ids = [artifact_id for _, artifact_id in image_descriptors]

        return {
            'descriptors': descriptors,
            'ids': ids
        }
