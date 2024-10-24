"""
This module defines API views for handling operations related to Artifacts, Metadata, 
and Artifact Downloads in the application.

Classes:
- ArtifactDetailAPIView: Provides a detail view for a single artifact. 
- MetadataListAPIView: Provides a list view for metadata related to artifacts. 
- ArtifactDownloadAPIView: Handles both the retrieval of detailed information about 
    an artifact and the creation of artifact requester records. 
- CustomPageNumberPagination: Provides paginated responses for API views.
- CatalogAPIView: Provides a list view for artifacts in the catalog.
- ArtifactCreateUpdateAPIView: Provides functionality for creating and updating artifacts.
- InstitutionAPIView: Provides a list view for institutions.
"""

import math
import zipfile
import pandas as pd
import time
import re
import shutil
from io import BytesIO
import logging
import os
from rest_framework import permissions, generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import Q
from django.core.files import File
from django.http import HttpResponse
from django.conf import settings
from .serializers import (
    ArtifactRequesterSerializer,
    ArtifactSerializer,
    CatalogSerializer,
    UpdateArtifactSerializer,
    InstitutionSerializer,
    ShapeSerializer,
    TagSerializer,
    CultureSerializer,
)
from .models import (
    Artifact,
    ArtifactRequester,
    CustomUser,
    Institution,
    Image,
    Shape,
    Tag,
    Culture,
    Model,
    Thumbnail,
)
from .permissions import IsFuncionarioPermission, IsAdminPermission
from .authentication import TokenAuthentication

logger = logging.getLogger(__name__)


class ArtifactDetailAPIView(generics.RetrieveAPIView):
    """
    A view that provides detail for a single artifact.

    It extends Django REST Framework's RetrieveAPIView.

    Attributes:
        queryset: Specifies the queryset that this view will use to retrieve
            the Artifact object. It retrieves all Artifact objects.
        serializer_class: Specifies the serializer class that should be used
            for serializing the Artifact object.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow any user to access this view.
    """

    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    permission_classes = [permissions.AllowAny]


class MetadataListAPIView(generics.ListAPIView):
    """
    A view that provides a list of metadata related to artifacts.

    It extends Django REST Framework's ListAPIView.

    Attributes:
        permission_classes: Defines the list of permissions that apply to this
            view. It is set to allow any user to access this view.
    """

    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests.

        It retrieves all shapes, tags, and cultures from the database, serializes them,
        and returns them in a response.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for shapes, tags, and cultures.
        """
        try:
            shapes = Shape.objects.all()
            tags = Tag.objects.all()
            cultures = Culture.objects.all()
            
            # Serialize the data
            shape_serializer = ShapeSerializer(shapes, many=True)
            tag_serializer = TagSerializer(tags, many=True)
            culture_serializer = CultureSerializer(cultures, many=True)

            # Function to change 'name' key to 'value'
            def rename_key(lst):
                return [{"id": item["id"], "value": item["name"]} for item in lst]
            # Combine the data with 'name' key changed to 'value'
            data = {
                "shapes": rename_key(shape_serializer.data),
                "tags": rename_key(tag_serializer.data),
                "cultures": rename_key(culture_serializer.data),
            }

            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Could not retrieve metadata:{e}")
            return Response({"detail": f"Error al obtener metadata"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ArtifactDownloadAPIView(generics.RetrieveAPIView, generics.CreateAPIView):
    """
    A view that provides downloaded data of detailed information about an artifact.

    Allows the creation of artifact requester records. It extends Django REST
    Framework's RetrieveAPIView and CreateAPIView.

    Attributes:
        queryset: Specifies the queryset that this view will use to retrieve
            the Artifact object. It retrieves all Artifact objects.
        serializer_class: Specifies the serializer class that should be used
            for serializing the Artifact object.
        lookup_field: Specifies the field that should be used to retrieve a
            single object from the queryset.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow any user to access this view.
    """

    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    lookup_field = "pk"
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests.

        It creates a new artifact requester record and returns a response containing
        the serialized data for the created artifact requester.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the created artifact requester.
        """
        logger.info(
            "Creating new artifact requester for artifact {}".format(kwargs.get("pk"))
        )
        # If the body is empty, retrieve info from backend
        if not request.data:
            token = request.headers.get("Authorization")
            try:
                token_instance = Token.objects.get(key=token.split(" ")[1])
            except Token.DoesNotExist:

                return Response(
                    {"detail": "Se requiere iniciar sesión nuevamente"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            username = token_instance.user
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                return Response(
                    {"detail": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
                )
            name = user.first_name + " " + user.last_name
            
            requester = ArtifactRequester.objects.create(
                name=name,
                rut=user.rut,
                email=user.email,
                is_registered=True,
                institution=user.institution if user.institution else None,
                artifact=Artifact.objects.get(pk=kwargs.get("pk")),
                )
            serializer = ArtifactRequesterSerializer(requester)
                
        else:
            try:
                
                requester = ArtifactRequester.objects.create(
                    name=request.data.get("fullName"),
                    rut=request.data.get("rut"),
                    email=request.data.get("email"),
                    comments=request.data.get("comments"),
                    is_registered=False,
                    institution=Institution.objects.get(pk=request.data.get("institution")),
                    artifact=Artifact.objects.get(pk=kwargs.get("pk")),
                )
                serializer = ArtifactRequesterSerializer(requester)
            except Exception as e:
                logger.error(f"Error al crear solicitante: {e}")
                return Response(
                    {"detail": "Error al crear solicitante"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests.

        It retrieves detailed information about an artifact and returns a response
        containing the serialized data for the artifact.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the artifact.
        """
        pk = kwargs.get("pk")
        if pk is not None:
            logger.info(f"Downloading artifact {pk}")
            try:
                artifact = Artifact.objects.get(pk=pk)
            except Artifact.DoesNotExist:
                return Response(
                    {"detail": "Pieza no encontrada"}, status=status.HTTP_404_NOT_FOUND
                )

            buffer = BytesIO()

            with zipfile.ZipFile(buffer, "w") as zipf:
                if artifact.id_thumbnail:
                    zipf.write(
                        artifact.id_thumbnail.path.path,
                        f"thumbnail/{artifact.id_thumbnail.path}",
                    )

                zipf.write(
                    artifact.id_model.texture.path,
                    f"model/{artifact.id_model.texture.name}",
                )
                zipf.write(
                    artifact.id_model.object.path,
                    f"model/{artifact.id_model.object.name}",
                )
                zipf.write(
                    artifact.id_model.material.path,
                    f"model/{artifact.id_model.material.name}",
                )

                images = Image.objects.filter(id_artifact=artifact.id)
                for image in images:
                    zipf.write(image.path.path, f"model/{image.path}")

            buffer.seek(0)

            response = HttpResponse(buffer, content_type="application/zip")
            response["Content-Disposition"] = f"attachment; filename=artifact_{pk}.zip"
            return response


class CustomPageNumberPagination(PageNumberPagination):
    """
    A custom pagination class that provides paginated responses for API views.

    It extends Django REST Framework's PageNumberPagination.

    Attributes:
        page_size: Specifies the number of items to display per page.
    """

    page_size = 9

    def get_paginated_response(self, data):
        """
        Retrieves paginated response data.

        Args:
            data: The data to be paginated.

        Returns:
            Response: Django REST Framework's Response object containing paginated data.
        """
        return Response(
            {
                "current_page": int(self.request.query_params.get("page", 1)),
                "total": self.page.paginator.count,
                "per_page": self.page_size,
                "total_pages": math.ceil(self.page.paginator.count / self.page_size),
                "data": data,
            }
        )


class CatalogAPIView(generics.ListAPIView):
    """
    A view that provides a list of artifacts in the catalog.

    It extends Django REST Framework's ListAPIView.

    Attributes:
        serializer_class: Specifies the serializer class that should be used
            for serializing the Artifact objects.
        pagination_class: Specifies the pagination class that should be used
            for paginating the response data.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow any user to access this view.
    """

    serializer_class = CatalogSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Retrieves the queryset for the view.

        Returns:
            queryset: The queryset containing all artifacts in the catalog.
        """
        queryset = Artifact.objects.all().order_by("id")

        # Filtros a partir de parámetros de consulta (query parameters)
        description = self.request.query_params.get("query", None)
        culture = self.request.query_params.get("culture", None)
        shape = self.request.query_params.get("shape", None)
        tags = self.request.query_params.get("tags", None)

        q_objects = Q()

        # Case insensitive search
        if description is not None:
            q_objects &= Q(description__icontains=description) | Q(id__icontains=description)
        if culture is not None:
            q_objects &= Q(id_culture__name__iexact=culture)
        if shape is not None:
            q_objects &= Q(id_shape__name__iexact=shape)
        if tags is not None:
            for tag in tags.split(","):
                q_objects &= Q(id_tags__name__iexact=tag.strip())

        # Filtramos el queryset con los q_objects
        filtered_queryset = queryset.filter(q_objects)
        return filtered_queryset

    def get_available_filters(self, filtered_queryset):
        """
        Obtiene las culturas, formas y etiquetas disponibles en el queryset filtrado.
        """
        available_cultures = Artifact.objects.filter(id__in=filtered_queryset).values_list('id_culture__name', flat=True).distinct()
        available_shapes = Artifact.objects.filter(id__in=filtered_queryset).values_list('id_shape__name', flat=True).distinct()
        available_tags = Artifact.objects.filter(id__in=filtered_queryset).values_list('id_tags__name', flat=True).distinct()

        available_filters = {
            "cultures": list(available_cultures),
            "shapes": list(available_shapes),
            "tags": list(available_tags),
        }
        print(available_filters)
        return available_filters

    def get_serializer_context(self):
        """
        Retrieves the context for the serializer.

        Returns:
            dict: A dictionary containing the request object.
        """
        return {"request": self.request}

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests.

        It retrieves all artifacts in the catalog, serializes them, and returns
        paginated data in a response.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing paginated
                data for the artifacts.
        """
        # Obtiene el queryset filtrado
        queryset = self.filter_queryset(self.get_queryset())
        
        # Obtiene los filtros únicos (culturas, formas, etiquetas)
        available_filters = self.get_available_filters(queryset)

        # Paginación si es necesario
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            page_data = self.get_paginated_response(serializer.data).data
            return Response({**page_data, "filters": available_filters})


        # Respuesta sin paginación
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data, "filters": available_filters}, status=status.HTTP_200_OK)


class ArtifactCreateUpdateAPIView(generics.GenericAPIView):
    """
    A view that provides functionality for creating and updating artifacts.

    It extends Django REST Framework's GenericAPIView.

    Attributes:
        queryset: Specifies the queryset that this view will use to retrieve
            the Artifact objects. It retrieves all Artifact objects.
        serializer_class: Specifies the serializer class that should be used
            for serializing the Artifact objects.
        lookup_field: Specifies the field that should be used to retrieve a
            single object from the queryset.
        authentication_classes: Defines the list of authentication classes that
            apply to this view. It is set to TokenAuthentication.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow only authenticated users with the
            role of 'Funcionario' or 'Administrador' to access this view.
    """

    queryset = Artifact.objects.all()
    serializer_class = UpdateArtifactSerializer
    lookup_field = "pk"
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        permissions.IsAuthenticated & (IsFuncionarioPermission | IsAdminPermission)
    ]

    def get_object(self):
        """
        Retrieves the object for the view.

        Returns:
            object: The object retrieved from the queryset based on the primary key.
        """
        pk = self.kwargs.get("pk")
        if pk is not None:
            return super().get_object()
        return None

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests.

        It creates a new artifact and returns a response containing the serialized
        data for the created artifact.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the created artifact.
        """
        return self.create_or_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests.

        It updates an existing artifact and returns a response containing the serialized
        data for the updated artifact.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the updated artifact.
        """
        return self.create_or_update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Handles PATCH requests.

        It partially updates an existing artifact and returns a response containing the
        serialized data for the updated artifact.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the updated artifact.
        """
        return self.create_or_update(request, *args, **kwargs, partial=True)

    def create_or_update(self, request, *args, **kwargs):
        """
        Creates or updates an artifact based on the request data.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the created or updated artifact.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if instance is None:
            logger.info("Creating new artifact")
            serializer = self.get_serializer(data=request.data)
            success_status = status.HTTP_201_CREATED
        else:
            logger.info(f"Updating artifact {instance.id}")
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            success_status = status.HTTP_200_OK

        serializer.is_valid(raise_exception=True)

        # Save the instance first
        instance = serializer.save()

        logger.info(f"Handle file uploads for artifact {instance.id}")
        # Handle file uploads
        try:
            self.handle_file_uploads(instance, request.FILES, request.data)
        except Exception as e:
            logger.error(f"Error al subir archivos: {e}")
            return Response(
                {"detail": f"Error al subir archivos"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Save again to ensure all related objects are properly linked
        instance.save()

        return Response(
            {"data": serializer.data},
            status=success_status,
        )

    def perform_create_or_update(self, serializer):
        """
        Performs the creation or update of an artifact based on the serializer.

        Args:
            serializer: The serializer object that contains the data for the artifact.
        """
        serializer.save()

    def handle_file_uploads(self, instance, files, data):
        """
        Handles file uploads for an artifact.

        Args:
            instance: The Artifact object for which the file uploads are being handled.
            files: The files to be uploaded.
            data: The data associated with the files.
        """
        # Handle thumbnail
        thumbnail_data = files.get("new_thumbnail")
        if thumbnail_data:
                # Upload file
                thumbnail_file = File(thumbnail_data, name=thumbnail_data.name)
                # Create Thumbnail instance
                thumbnail = Thumbnail.objects.create(path=thumbnail_file)
                logger.info(f"Thumbnail created: {thumbnail.path}")
                # Set the thumbnail
                instance.id_thumbnail = thumbnail
        else:
            thumbnail_name = data.get("thumbnail", None)
            if thumbnail_name:
                thumbnail_path = os.path.join(settings.THUMBNAILS_URL, thumbnail_name)
                thumbnail = Thumbnail.objects.get(path=thumbnail_path)
                instance.id_thumbnail = thumbnail
                logger.info(f"Thumbnail kept: {thumbnail.path}")
            else:
                instance.id_thumbnail = None
                logger.info("Thumbnail removed")

        # Handle model files
        # New files
        # check if model files are sent in the request
        new_texture_file = files.get("model[new_texture]")
        new_object_file = files.get("model[new_object]")
        new_material_file = files.get("model[new_material]")
        print(new_texture_file, new_object_file, new_material_file)

        new_texture_instance, new_object_instance, new_material_instance = (
            None,
            None,
            None,
        )
        if new_texture_file:
            new_texture_instance = File(new_texture_file, name=new_texture_file.name)
            logger.info(f"New texture file: {new_texture_instance}")
        if new_object_file:
            new_object_instance = File(new_object_file, name=new_object_file.name)
            logger.info(f"New object file: {new_object_instance}")
        if new_material_file:
            new_material_instance = File(new_material_file, name=new_material_file.name)
            logger.info(f"New material file: {new_material_instance}")

        # Update Model instance
        # It allows to create a new model with only the new files
        if not new_texture_instance and not new_object_instance and not new_material_instance:
            model = None
        else:
            model, created = Model.objects.get_or_create(
                texture=(
                    new_texture_instance
                    if new_texture_instance
                    else None if not instance.id_model else instance.id_model.texture
                ),
                object=(
                    new_object_instance 
                    if new_object_instance 
                    else None if not instance.id_model else instance.id_model.object
                ),
                material=(
                    new_material_instance
                    if new_material_instance
                    else None if not instance.id_model else instance.id_model.material
                ),
            )
            if created:
                logger.info(
                    f"Model created: {model.texture}, {model.object}, {model.material}"
                )
            else:
                logger.info(
                    f"Model updated: {model.texture}, {model.object}, {model.material}"
                )
        # Set the model
        instance.id_model = model

        # Handle images
        # Get the images that are already uploaded and should be kept, and the new images to be uploaded
        # Old images are unlinked. This way we can set an empty list of images if we want to remove all images

        # First we get the images linked to the artifact
        old_images = Image.objects.filter(id_artifact=instance)
        # We update them so they are not linked to the artifact anymore
        for image in old_images:
            image.id_artifact = None
            image.save()
            logger.info(f"Image unlinked: {image.path}")

        # Now we recover the images that should be kept
        keep_images = data.getlist(
            "images", []
        )  # images are paths from photos already uploaded
        for image_name in keep_images:
            # Update instances
            image_path = os.path.join(settings.IMAGES_URL, image_name)
            image = Image.objects.get(path=image_path)
            image.id_artifact = instance
            image.save()
            logger.info(f"Image updated: {image.path}")

        new_images = files.getlist(
            "new_images", []
        )  # new_images are files to be uploaded
        for image_data in new_images:
            image_file = File(image_data, name=image_data.name)
            # Create Image instance
            image = Image.objects.create(id_artifact=instance, path=image_file)
            logger.info(f"Image created: {image.path}")


class BulkLoadingAPIView(generics.GenericAPIView):
    """
    A view that provides functionality for bulk loading artifacts.

    It extends Django REST Framework's GenericAPIView.

    Attributes:
        queryset: Specifies the queryset that this view will use to retrieve
            the Artifact objects. It retrieves all Artifact objects.
        serializer_class: Specifies the serializer class that should be used
            for serializing the Artifact objects.
        authentication_classes: Defines the list of authentication classes that
            apply to this view. It is set to TokenAuthentication.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow only authenticated users with the
            role of 'Funcionario' or 'Administrador' to access this view.
    """

    queryset = Artifact.objects.all()
    serializer_class = UpdateArtifactSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        permissions.IsAuthenticated & (IsFuncionarioPermission | IsAdminPermission)
    ]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests.

        It bulk loads artifacts and returns a response containing the serialized
        data for the created artifacts.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the created artifacts.
        """
        errores = []
        logger.info("Bulk loading artifacts")
        try:
            zip_file = request.FILES.get("zip")
            excel_file = request.FILES.get("excel")
        except KeyError:
            return Response(
                {"detail": "Se requiere un archivo ZIP y un archivo Excel"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Check if the files are ZIP and Excel files
        if not zipfile.is_zipfile(zip_file):
            return Response(
                {"detail": "El archivo ZIP no es válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not excel_file.name.endswith(".xlsx"):
            return Response(
                {"detail": "El archivo Excel no es válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Read the Excel file
        try:
            artifacts = self.read_excel(excel_file)
            logger.info(f"Excel file read: {artifacts.head()}")
        except Exception as e:
            logger.error(f"Error al leer el archivo Excel: {e}")
            return Response(
                {"detail": "Error al leer el archivo Excel"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        #validate the excel file
        valid, errors = self.validate_data(artifacts)
        if not valid:
            return Response(
                {"detail": "Error al validar el archivo Excel", "errores": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Unzip the ZIP file and put the files in a temporary folder
        temp_dir = settings.MEDIA_ROOT+"temp/"+str(hash(zip_file.name+str(time.time())))
        try:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            logger.error(f"Error al extraer el archivo ZIP: {e}")
            return Response(
                {"detail": "Error al extraer el archivo ZIP"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        #list all files in the temp folder
        files = self.list_files(temp_dir)
        files_not_temp_path = [file.replace(temp_dir, "") for file in files]
        files_not_temp_path = [os.path.normpath(file) for file in files_not_temp_path]
        #validar que los archivos necesarios estén en el zip
        valid, errors, data_with_files = self.validate_files(artifacts, files_not_temp_path)
        if not valid:
            self.delete_files(temp_dir)
            return Response(
                {"detail": "Error al validar los archivos", "errores": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Iterate over the artifacts and create or update them
        for data in data_with_files:
            try:
                #buscar etiquetas
                tags_instances = []
                for tag in data["tags"]:
                    tag_instance = Tag.objects.get(name=tag)
                    tags_instances.append(tag_instance)
                
                #buscar la cultura
                culture_instance = Culture.objects.get(name=data["culture"])

                #buscar la forma
                shape_instance = Shape.objects.get(name=data["shape"])

                #descripción
                description = data["description"]

                #buscar algun archivo de thumbnail
                thumbnail = data["file_thumbnail"]
                thumbnail_path = os.path.normpath(temp_dir + thumbnail)
                with open(thumbnail_path, "rb") as f:
                    thumbnail_file = File(f, name=thumbnail)
                    thumbnail_instance = Thumbnail.objects.create(path=thumbnail_file)

                #buscar los archivos de modelo
                models = data["files_model"]
                texture_file = [file for file in models if file.endswith(".jpg")]
                object_file = [file for file in models if file.endswith(".obj")]
                material_file = [file for file in models if file.endswith(".mtl")]
                if texture_file != [] and object_file != [] and material_file != []:
                    texture_path = os.path.normpath(temp_dir + texture_file[0])
                    object_path = os.path.normpath(temp_dir + object_file[0])
                    material_path = os.path.normpath(temp_dir + material_file[0])
                    with open(texture_path, "rb") as f:
                        texture_file = File(f, name=texture_file[0])
                        with open(object_path, "rb") as f:
                            object_file = File(f, name=object_file[0])
                            with open(material_path, "rb") as f:
                                material_file = File(f, name=material_file[0])
                                model, created = Model.objects.get_or_create(
                                    texture=texture_file,
                                    object=object_file,
                                    material=material_file,
                                )
                    if created:
                        logger.info(f"Model created: {model.texture}, {model.object}, {model.material}")
                    else:
                        logger.info(f"Model updated: {model.texture}, {model.object}, {model.material}")
                else:
                    model = None

                # crear la pieza
                artifact = Artifact.objects.create(
                    description=description,
                    id_thumbnail=thumbnail_instance,
                    id_model=model,
                    id_shape=shape_instance,
                    id_culture=culture_instance,
                )
                artifact.save()
                #imagenes
                images = data["files_images"]
                images_instances = []
                for image in images:
                    image_path = os.path.normpath(temp_dir + image)
                    with open(image_path, "rb") as f:
                        image_file = File(f, name=image)
                        image_instance = Image.objects.create(path=image_file, id_artifact=artifact)
                        images_instances.append(image_instance)

                for tag_instance in tags_instances:
                    artifact.id_tags.add(tag_instance)
            except Exception as e:
                self.delete_files(temp_dir)
                return Response(
                    {"detail": f"Error al cargar las piezas: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Delete the temporary folder and its contents
        self.delete_files(temp_dir)

        
        return Response(
            {"detail": "Carga masiva exitosa"},
            status=status.HTTP_201_CREATED,
        )

    def read_excel(self, excel_file) -> pd.DataFrame:
        """
        Reads an Excel file containing artifact data.

        Args:
            excel_file: The Excel file to be read.

        Returns:
            DataFrame: A Pandas DataFrame containing the data from the Excel file
        """
        excel = pd.read_excel(excel_file, engine="openpyxl", header=0)
        return excel

    def validate_data(self, data: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Validates the data read from the Excel file.

        Args:
            data: The data read from the Excel file.

        Returns:
            bool: A boolean indicating whether the data is valid.
            list[str]: A list of error messages.
        """
        valid = True
        errors = []
        #chequeamos que tenga 5 columnas sin nulls
        if data.shape[1] != 5:
            valid = False
            errors.append("El archivo Excel debe tener 5 columnas: id o nombre, descripción, forma, cultura, etiquetas")
        
        for index, row in data.iterrows():
            # chequeamos que no haya filas con nulls
            if row.isnull().values.any():
                valid = False
                errors.append(f"La fila {index+2} tiene valores nulos")
                continue
            #chequeamos que la columna de cultura tenga solo culturas existentes
            if not Culture.objects.filter(name=row.iloc[3]).exists():
                valid = False
                errors.append(f"La fila {index+2} tiene una cultura inexistente: {row.iloc[3]}")
            #chequeamos que la columna de tags tenga solo tags existentes
            tags = row.iloc[4].split(",")
            for tag in tags:
                if not Tag.objects.filter(name=tag).exists():
                    valid = False
                    errors.append(f"La fila {index+2} tiene una etiqueta inexistente: {tag}")
            #chequeamos que la columna de forma tenga solo formas existentes
            if not Shape.objects.filter(name=row.iloc[2]).exists():
                valid = False
                errors.append(f"La fila {index+2} tiene una forma inexistente: {row.iloc[2]}")
        return valid, errors 

    def list_files(self, path: str) -> list:
        """
        Lists files in a directory and its subdirectories.

        Args:
        path: The path to the directory.

        Returns:
        list: A list of files in the directory and its subdirectories.
        """
        file_list = []
        if os.path.isdir(path):
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    file_list.extend(self.list_files(full_path))
                elif os.path.isfile(full_path):
                    file_list.append(full_path)
        return file_list

    def validate_files(self, data: pd.DataFrame, files: list) -> tuple[bool, list[str], list]:
        """
        Validates the files in the ZIP file based on the data from the Excel file.

        Args:
            data: The data from the Excel file.
            files: The files in the ZIP file.

        Returns:
            bool: A boolean indicating whether the files are valid.
            list: A list of error messages.
            list: A list of dictionaries containing the data for the artifacts and their files.
        """
        valid = True
        errors = []
        files_filtered = files
        data_with_files = []
        pattern = lambda id: re.compile(rf"(^.*[\/\\]+0*{re.escape(id)}[.\,/_\\-]+.*$)")
        for index, row in data.iterrows():
            id = str(row.iloc[0])
            files_row = [file for file in files_filtered if pattern(id).search(file)]
            if len(files_row) == 0:
                valid = False
                errors.append(f"La pieza {id} no tiene archivos asociados")
                continue
            else:
                thumbnail = [file for file in files_row if "thumbnail" in file]
                if thumbnail == []:
                    valid = False
                    errors.append(f"La pieza {id} no tiene thumbnail")
                elif len(thumbnail) > 1:
                    valid = False
                    errors.append(f"La pieza {id} tiene más de un thumbnail: {thumbnail}")
                model_files = [file for file in files_row if "obj" in file]
                obj = [file for file in model_files if file.endswith(".obj")]
                mtl = [file for file in model_files if file.endswith(".mtl")]
                jpg = [file for file in model_files if file.endswith(".jpg")]
                images = [file for file in files_row if (("jpg" in file) or ("png" in file))
                           and file not in thumbnail and file not in model_files]
                if len(images) == 0 and (len(obj) == 0 or len(mtl) == 0 or len(jpg) == 0):
                    valid = False
                    if len(obj) == 0:
                        errors.append(f"La pieza {id} no tiene archivo .obj")
                    if len(mtl) == 0:
                        errors.append(f"La pieza {id} no tiene archivo .mtl")
                    if len(jpg) == 0:
                        errors.append(f"La pieza {id} no tiene archivo .jpg")
                    if len(images) == 0:
                        errors.append(f"La pieza {id} no tiene imágenes ni modelo")
                else:
                    data_with_files.append({
                        "description": row.iloc[1],"shape": row.iloc[2], "culture": row.iloc[3], "tags": row.iloc[4].split(","), "file_thumbnail": thumbnail[0], "files_model": model_files, "files_images": images})
                files_filtered = [file for file in files_filtered if file not in files_row]
        return valid, errors, data_with_files

    def delete_files(self, path: str):
        """
        Deletes files in a directory and its subdirectories.

        Args:
            path: The path to the directory.
        """
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Deleted directory: {path}")
            else:
                os.remove(path)
                logger.info(f"Deleted file: {path}")
        except Exception as e:
            logger.error(f"Error al eliminar archivos: {e}")


class InstitutionAPIView(generics.ListCreateAPIView):
    """
    A view that provides a list of institutions.

    It extends Django REST Framework's ListCreateAPIView.

    Attributes:
        queryset: Specifies the queryset that this view will use to retrieve
            the Institution objects. It retrieves all Institution objects.
        serializer_class: Specifies the serializer class that should be used
            for serializing the Institution objects.
        permission_classes: Defines the list of permissions that apply to
            this view. It is set to allow any user to access this view.
    """
    queryset = Institution.objects.all().order_by("id")
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests.

        It retrieves all institutions, serializes them, and returns them in a response.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Django REST Framework's Response object containing serialized
                data for the institutions.
        """
        try:
            institutions = Institution.objects.all()

            # Serialize the data
            institution_serializer = InstitutionSerializer(institutions, many=True)
            # Function to change 'name' key to 'value'
            def rename_key(lst):
                return [{"id": item["id"], "value": item["name"]} for item in lst]
            data = rename_key(institution_serializer.data)
            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Could not retrieve institutions:{e}")
            return Response({"detail": f"Error al obtener instituciones"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)