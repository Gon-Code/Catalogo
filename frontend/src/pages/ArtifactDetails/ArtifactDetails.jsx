import React, { useEffect, useState } from "react";
import {
  Typography,
  Button,
  Chip,
  Skeleton,
  CircularProgress,
} from "@mui/material";
import { Category, Diversity3, LocalOffer } from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import DownloadArtifactButton from "./components/DownloadArtifactButton";
import ModelVisualization from "./components/ModelVisualization";
import ImageVisualization from "./components/ImageVisualization";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import DownloadArtifactForm from "./components/DownloadArtifactForm";
import NotFound from "../../components/NotFound";
import { API_URLS } from "../../api";
import { useToken } from "../../hooks/useToken";
import { useSnackBars } from "../../hooks/useSnackbars";
import Carousel from "./components/Carousel";

/**
 * The ArtifactDetails component displays detailed information about a specific artifact,
 * including its model, images, attributes, and provides options for download and editing.
 * It handles data fetching, state management, and conditional rendering based on user authentication.
 * @returns {JSX.Element} Component for displaying artifact details.
 */
const ArtifactDetails = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = useToken();
  const { addAlert } = useSnackBars();
  const loggedIn = !!token;
  const { artifactId } = useParams();
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [artifact, setArtifact] = useState({
    attributes: {
      culture: { id: "", value: "" },
      shape: { id: "", value: "" },
      tags: [],
      description: "",
    },
    thumbnail: "",
    model: {
      object: "",
      material: "",
      texture: "",
    },
    images: [],
  });
  const [selectedVisualization, setSelectedVisualization] = useState({
    type: "",
    index: 0,
  })

  /**
   * Redirects the user to the edit page of the current artifact.
   */
  const handleRedirect = () => {
    navigate(`/catalog/${artifactId}/edit`, {
      state: { from: location },
    });
  };

  useEffect(() => {
    /**
     * Fetches detailed information about the artifact from the API.
     * Sets the artifact state if successful; sets notFound state if artifact not found.
     */
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
        setArtifact(response);
        if (response.model.object !== "") {
          setSelectedVisualization({
            type: "model",
            index: -1
          })
          console.log("model visualization")
        } else {
          setSelectedVisualization({
            type: "image",
            index: 0
          })
          console.log("image visualization")
        }
      })
      .finally(() =>{
        setLoading(false)
      });
  }, [artifactId, token]);

  /**
   * Handles the download functionality for the artifact.
   * Initiates download and displays alerts for success or failure.
   */
  const handleDownload = async () => {
    try {
      const response = await fetch(
        `${API_URLS.DETAILED_ARTIFACT}/${artifactId}/download`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        addAlert(data.detail);
        return;
      }

      // If the first fetch was successful, proceed with downloading the artifact
      const downloadResponse = await fetch(
        `${API_URLS.DETAILED_ARTIFACT}/${artifactId}/download`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const url = window.URL.createObjectURL(
        new Blob([await downloadResponse.blob()])
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = `artifact_${artifactId}.zip`;
      link.click();
      link.remove();
      addAlert("Descarga exitosa");
    } catch (error) {
      addAlert("Error al descargar pieza");
    }
  };


  const handleVisualization = (index) => {
    if (index === -1) {
      setSelectedVisualization({
        type: "model",
        index: -1
      })
    } else {
      setSelectedVisualization({
        type: "image",
        index: index
      })
    }
  }

  return (
    <>
      {notFound ? (
        // Renders a NotFound component if the artifact is not found
        <NotFound />
      ) : (
        // Renders artifact details if found
        <ContainerGrid>
          {/* LeftBox: Contains artifact title, download/edit buttons, model visualization, and image carousel */}
          <LeftBox>
            <CustomContainer>
              {/* Artifact title */}
              <Typography variant="h4">
                <b>Pieza {artifact.id}</b>
              </Typography>
              {/* Conditional rendering based on user authentication */}
              {loggedIn ? (
                // Buttons for download and edit (if logged in)
                <HorizontalStack>
                  <Button variant="contained" onClick={handleDownload}>
                    Descargar Pieza
                  </Button>
                  <Button variant="contained" onClick={handleRedirect}>
                    Editar Pieza
                  </Button>
                </HorizontalStack>
              ) : (
                // Button to request data if not logged in
                <DownloadArtifactButton text={"Solicitar datos"}>
                  <DownloadArtifactForm artifactInfo={artifact} />
                </DownloadArtifactButton>
              )}
            </CustomContainer>
            {/* Loading indicator while model is being loaded */}
            {loading ? (
              <CustomDiv>
                <CircularProgress color="primary" />
              </CustomDiv>
            ) : (
              <>
              {selectedVisualization.type === "image" ? (
                <ImageVisualization imagePath={artifact.images[selectedVisualization.index]} />
              ) : (
              // Renders 3D model visualization if object and material paths are available
              <ModelVisualization
                objPath={artifact.model.object}
                mtlPath={artifact.model.material}
              />
              )}
              </>
            )}
            {/* Image carousel for displaying artifact images */}
            <Carousel images={artifact.images} thumbnail={artifact.thumbnail} modelExists={!!artifact.model.object} selectVisualization={handleVisualization} />
          </LeftBox>
          {/* RightBox: Contains artifact description, tags, and attributes */}
          <RightBox>
            {/* Displays artifact description or loading skeleton */}
            <Typography>
              {loading ? (
                <CustomSkeletonText />
              ) : (
                artifact.attributes.description
              )}
            </Typography>
            {/* Displays artifact shape tag */}
            <HorizontalStack>
              <Typography variant="h5">
                <Category color="inherit" fontSize="small" style={{ verticalAlign: 'middle' }} /> Forma:{" "}
              </Typography>
              {loading ? (
                <CustomSkeletonTag />
              ) : (
                <CustomShapeTag label={artifact.attributes.shape.value} />
              )}
            </HorizontalStack>
            {/* Displays artifact culture tag */}
            <HorizontalStack>
              <Typography variant="h5">
                {" "}
                <Diversity3 color="inherit" fontSize="small" style={{ verticalAlign: 'middle' }} /> Cultura:
              </Typography>
              {loading ? (
                <CustomSkeletonTag />
              ) : (
                <CustomCultureTag label={artifact.attributes.culture.value} />
              )}
            </HorizontalStack>
            {/* Displays artifact tags */}
            <VerticalStack>
              <Typography variant="h5">
                <LocalOffer color="inherit" fontSize="small" style={{ verticalAlign: 'middle' }} /> Etiquetas:
              </Typography>
              <TagContainer>
                {loading ? (
                  <CustomSkeletonTag />
                ) : artifact.attributes.tags.length > 0 ? (
                  artifact.attributes.tags.map((tag) => (
                    <Chip key={tag.id} label={tag.value} />
                  ))
                ) : (
                  <p>Sin etiquetas</p>
                )}
              </TagContainer>
            </VerticalStack>
          </RightBox>
        </ContainerGrid>
      )}
    </>
  );
};

// Styled components for customizing UI elements
const CustomContainer = styled("div")(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  justifyContent: "space-between",
  alignItems: "center",
  width: "100%",
  height: theme.spacing(5.25),
}));

const HorizontalStack = styled("div")(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  gap: theme.spacing(1),
}));

const VerticalStack = styled("div")(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(1),
}));

const LeftBox = styled("div")(({ theme }) => ({
  width: theme.spacing(83),
  [theme.breakpoints.up("md")]: {
    width: theme.spacing(106.5),
  },
  [theme.breakpoints.up("xl")]: {
    width: theme.spacing(140),
  },
  [theme.breakpoints.up("xxl")]: {
    width: theme.spacing(175.5),
  },
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "flex-start",
  gap: theme.spacing(1),
}));

const RightBox = styled("div")(({ theme }) => ({
  padding: theme.spacing(1),
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
  backgroundColor: "#fff",
  [theme.breakpoints.down("md")]: {
    width: theme.spacing(83),
    minWidth: theme.spacing(83),
  },
  [theme.breakpoints.up("md")]: {
    width: theme.spacing(104.5),
  },
  [theme.breakpoints.up("lg")]: {
    marginTop: theme.spacing(6.25),
    width: theme.spacing(28),
    height: theme.spacing(69),
    gap: theme.spacing(1.7),
  },
  [theme.breakpoints.up("xl")]: {
    width: theme.spacing(34.25),
  },
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(3),
}));

const ContainerGrid = styled("div")(({ theme }) => ({
  marginTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
  display: "flex",
  justifyContent: "center",
  flexWrap: "wrap",
  paddingRight: theme.spacing(5),
  paddingLeft: theme.spacing(5),
  gap: theme.spacing(1),
  [theme.breakpoints.up("lg")]: {
    gap: theme.spacing(3),
  },
}));

const TagContainer = styled("div")(({ theme }) => ({
  display: "flex",
  flexWrap: "wrap",
  flexDirection: "row",
  width: "100%",
  gap: theme.spacing(1),
}));

const CustomShapeTag = styled(Chip)(({ theme }) => ({
  backgroundColor: theme.palette.tags.shape,
}));

const CustomCultureTag = styled(Chip)(({ theme }) => ({
  backgroundColor: theme.palette.tags.culture,
}));

const CustomSkeletonTag = styled(Skeleton)(({ theme }) => ({
  width: theme.spacing(13),
  height: theme.spacing(8),
  variant: "rounded",
}));

const CustomSkeletonText = styled(Skeleton)(({ theme }) => ({
  width: theme.spacing(28),
  height: theme.spacing(10),
  variant: "text",
}));

const CustomDiv = styled("div")(({ theme }) => ({
  width: "100%",
  height: theme.spacing(75),
  backgroundColor: "#2e2d2c",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
}));

export default ArtifactDetails;

