import React, { useState, useEffect } from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";
import {
  Container,
  Grid,
  Typography,
  Button,
  TextField,
  FormLabel,
  Box,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import UploadButton from "../../sharedComponents/UploadButton";
import AutocompleteExtended from "../../sharedComponents/AutocompleteExtended";
import { API_URLS } from "../../../api";
import ImageUploader from "./ImageUploader";
import NotFound from "../../../components/NotFound";
import { useSnackBars } from "../../../hooks/useSnackbars";
import { useToken } from "../../../hooks/useToken";
import { allowedFileTypes } from "../../Catalog/CreateArtifact";

/**
 * EditArtifact component allows editing artifact details, including uploads, descriptions, and metadata.
 * @returns {JSX.Element} Component for editing artifact details.
 */
const EditArtifact = () => {
  const navigate = useNavigate(); // Navigation hook for redirection
  const location = useLocation(); // Location hook for current route information
  const { artifactId } = useParams(); // Retrieves parameters from the route
  const { addAlert } = useSnackBars(); // Accesses addAlert function from SnackbarProvider
  const { token } = useToken(); // Retrieves authentication token from TokenProvider

  // State variables for managing component state
  const [notFound, setNotFound] = useState(false); // State for indicating if artifact is not found
  const [updatedArtifact, setUpdatedArtifact] = useState({ // State for storing updated artifact data
    object: "",
    texture: "",
    material: "",
    thumbnail: "",
    images: [],
    description: "",
    shape: {
      id: "",
      value: "",
    },
    culture: {
      id: "",
      value: "",
    },
    tags: [],
  });

  const [loading, setLoading] = useState(true); // State for indicating loading state
  const [errors, setErrors] = useState(false); // State for indicating errors

  const goBack = !!location.state?.from; // Determines if user should navigate back

  // State variables for storing API data
  const [shapeOptions, setShapeOptions] = useState([]); // State for storing shape options
  const [cultureOptions, setCultureOptions] = useState([]); // State for storing culture options
  const [tagOptions, setTagOptions] = useState([]); // State for storing tag options
  
  // require all model 3d data if you put one of them
  const [requiredModelData, setRequiredModelData] = useState(false);

  useEffect(() => {
    if (updatedArtifact.object || updatedArtifact.texture || updatedArtifact.material) {
      setRequiredModelData(true);
    } else {
      setRequiredModelData(false);
    }
  }, [updatedArtifact.object, updatedArtifact.texture, updatedArtifact.material]);


  // Fetch artifact data from the API
  useEffect(() => {
    fetch(`${API_URLS.DETAILED_ARTIFACT}/${artifactId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 404) {
            setNotFound(true);
            return;
          }
        }
        return response.json();
      })
      .then((response) => {
        let { attributes, thumbnail, model, images } = response;
        // Update state with fetched artifact data
        setUpdatedArtifact({
          thumbnail: thumbnail,
          images: images,
          ...model,
          ...attributes,
        });
      });
  }, [artifactId, token]);

  // Fetch metadata options from the API
  useEffect(() => {
    fetch(API_URLS.ALL_METADATA, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(response.statusText);
        }
        return response.json();
      })
      .then((data) => {
        let metadata = data.data;
        let shapes = metadata.shapes;
        let cultures = metadata.cultures;
        let tags = metadata.tags;

        // Update state with fetched metadata
        setShapeOptions(shapes);
        setCultureOptions(cultures);
        setTagOptions(tags);
      })
      .catch((error) => {
        setErrors(true);
        addAlert(error.message);
      })
      .finally(() => setLoading(false));
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handles input change events and updates state
  const handleInputChange = (name, value) => {
    setUpdatedArtifact({ ...updatedArtifact, [name]: value });
  };

  // Handles form submission for updating artifact
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (requiredModelData){
      if (!updatedArtifact.object || !updatedArtifact.texture || !updatedArtifact.material) {
        addAlert("Por favor, sube los archivos necesarios para el modelo 3D.");
        return;
      }
    } else {
      if (updatedArtifact.images.length === 0) {
        addAlert("Por favor, sube al menos una imagen del objeto.");
        return;
      }
    }

    const formData = new FormData();

    // Append new files or file names to form data
    if (updatedArtifact.object instanceof File) {
      formData.append("model[new_object]", updatedArtifact.object);
    }
    if (updatedArtifact.texture instanceof File) {
      formData.append("model[new_texture]", updatedArtifact.texture);
    }
    if (updatedArtifact.material instanceof File) {
      formData.append("model[new_material]", updatedArtifact.material);
    }
    if (updatedArtifact.thumbnail instanceof File) {
      formData.append("new_thumbnail", updatedArtifact.thumbnail);
    } else if (typeof updatedArtifact.thumbnail === "string") {
      formData.append(
        "thumbnail",
        updatedArtifact.thumbnail.split("/").pop()
      );
    }

    updatedArtifact.images.forEach((image) => {
      if (image instanceof File) {
        formData.append("new_images", image);
      } else if (typeof image === "string") {
        formData.append("images", image.split("/").pop());
      }
    });

    formData.append("description", updatedArtifact.description);
    formData.append("id_shape", updatedArtifact.shape.id);
    formData.append("id_culture", updatedArtifact.culture.id);

    updatedArtifact.tags.forEach((tag) =>
      formData.append("id_tags", tag.id)
    );

    // Send update request to API
    await fetch(
      `${API_URLS.DETAILED_ARTIFACT}/${artifactId}/update`,
      {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(response.statusText);
        }
        return response.json();
      })
      .then(() => {
        addAlert("¡Objeto editado con éxito!");
        navigate(`/catalog/${artifactId}`);
      })
      .catch((error) => {
        addAlert(error.message);
      });
  };

  // Utility function to get filename or URL from item
  const getFileNameOrUrl = (item) => {
    if (typeof item === "object" && item !== null) {
      return item.name;
    }
    if (typeof item === "string" && item.includes("/")) {
      return item.split("/").pop();
    }
    return item;
  };

  // Handles cancellation and navigation
  const handleCancel = () => {
    const from = goBack ? location.state.from : `/catalog`;
    navigate(from, { replace: goBack });
  };

  return (
    <>
      {notFound ? (
        <NotFound />
      ) : (
        <Container>
          <Box component="form" autoComplete="off" onSubmit={handleSubmit}>
            <Grid container rowGap={4}>
              <CustomTypography variant="h1">
                Editar pieza {artifactId}
              </CustomTypography>
              <Grid container spacing={2}>
                {/* Column for file uploads and image upload */}
                <ColumnGrid item xs={6} rowGap={2}>
                  <UploadButton
                    label={requiredModelData ? "Objeto *" : "Objeto"}
                    name="object"
                    isRequired={requiredModelData}
                    setStateFn={setUpdatedArtifact}
                    initialFilename={getFileNameOrUrl(
                      updatedArtifact.object
                    )}
                  />
                  <UploadButton
                    label={requiredModelData ? "Textura *" : "Textura"}
                    name="texture"
                    isRequired={requiredModelData}
                    setStateFn={setUpdatedArtifact}
                    initialFilename={getFileNameOrUrl(
                      updatedArtifact.texture
                    )}
                  />
                  <UploadButton
                    label={requiredModelData ? "Material *" : "Material"}
                    name="material"
                    isRequired={requiredModelData}
                    setStateFn={setUpdatedArtifact}
                    initialFilename={getFileNameOrUrl(
                      updatedArtifact.material
                    )}
                  />
                  <UploadButton
                    label="Miniatura (opcional)"
                    name="thumbnail"
                    setStateFn={setUpdatedArtifact}
                    initialFilename={getFileNameOrUrl(
                      updatedArtifact.thumbnail
                    )}
                  />
                  <ImageUploader
                    label="Imágenes (opcional)"
                    name="images"
                    images={updatedArtifact.images}
                    onListChange={setUpdatedArtifact}
                    allowedImageTypes={allowedFileTypes.images}
                  />
                </ColumnGrid>

                {/* Column for description, shape, culture, and tags */}
                <ColumnGrid item xs={6} rowGap={1}>
                  <FormLabel component="legend">Descripción *</FormLabel>
                  <TextField
                    required
                    id="description"
                    name="description"
                    placeholder="Descripción del objeto"
                    multiline
                    rows={4}
                    fullWidth
                    value={updatedArtifact.description}
                    onChange={(e) =>
                      handleInputChange(e.target.name, e.target.value)
                    }
                  />
                  <FormLabel component="legend">Forma *</FormLabel>
                  <AutocompleteExtended
                    id="shape"
                    name="shape"
                    value={updatedArtifact.shape}
                    setValue={handleInputChange}
                    options={shapeOptions}
                    placeholder="Seleccionar la forma del objeto"
                    isRequired
                    fullWidth
                    filterSelectedOptions
                    disabled={loading || errors}
                  />
                  <FormLabel component="legend">Cultura *</FormLabel>
                  <AutocompleteExtended
                    id="culture"
                    name="culture"
                    value={updatedArtifact.culture}
                    setValue={handleInputChange}
                    options={cultureOptions}
                    placeholder="Seleccionar la cultura del objeto"
                    isRequired
                    fullWidth
                    filterSelectedOptions
                    disabled={loading || errors}
                  />
                  <FormLabel component="legend">Etiquetas (opcional)</FormLabel>
                  <AutocompleteExtended
                    multiple
                    limitTags={3}
                    fullWidth
                    id="tags"
                    name="tags"
                    value={updatedArtifact.tags}
                    setValue={handleInputChange}
                    options={tagOptions}
                    placeholder="Seleccionar las etiquetas del objeto"
                    filterSelectedOptions
                    disabled={loading || errors}
                  />
                </ColumnGrid>
              </Grid>

              {/* Buttons for cancel and update */}
              <Grid container justifyContent="flex-end" columnGap={2}>
                <Button
                  variant="text"
                  color="secondary"
                  onClick={handleCancel}
                >
                  {goBack ? "Cancelar" : "Volver al catálogo"}
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  type="submit"
                >
                  Actualizar
                </Button>
              </Grid>
            </Grid>
          </Box>
        </Container>
      )}
    </>
  );
};

// Styled components for custom typography and grid columns
const CustomTypography = styled(Typography)(({ theme }) => ({
  marginTop: theme.spacing(6),
  textAlign: "left",
}));

const ColumnGrid = styled(Grid)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
}));

export default EditArtifact;
