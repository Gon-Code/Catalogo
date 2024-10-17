import React, { useEffect } from "react";
import styled from "@mui/material/styles/styled";

/**
 * Carousel component displays a carousel of images with a thumbnail for a 3D model.
 * Each image can be clicked to view in a larger size using the selectVisualization function.
 * @param {Object} props - Component props.
 * @param {string[]} props.images - Array of image paths to be displayed.
 * @param {string} props.thumbnail - Path to the thumbnail image for the 3D model.
 * @param {boolean} props.modelExists - Boolean indicating if a 3D model exists.
 * @param {Function} props.selectVisualization - Function to select a visualization.
 * @returns {JSX.Element|null} Component for displaying a carousel of images.
 */
const Carousel = ({images, thumbnail, modelExists, selectVisualization}) => {
    const [length, setLength] = React.useState(images.length);

    // Update the length of the carousel based on the number of images and if the model exists
    useEffect(() => {
        modelExists ? setLength(images.length + 1) : setLength(images.length);
    }, [images, modelExists]);

    return (
        length > 1 && (
            <CustomBox>
                <CustomImageList>
                    {/* Display the thumbnail image for the 3D model */}
                    {modelExists && (
                        <CustomImageListItem>
                            <CustomImage src={thumbnail} alt="Artifact" onClick={() => selectVisualization(-1)} />
                        </CustomImageListItem>
                    )}
                    {/* Maps through the images array to display each image */}
                    {images.map((item, index) => (
                        <CustomImageListItem key={index}>
                            <CustomImage src={item} alt="Artifact" onClick={() => selectVisualization(index)} />
                        </CustomImageListItem>
                    ))}
                </CustomImageList>
            </CustomBox>
        )
    );
};

// Styled components for custom styling
const CustomImageList = styled("div")(({ theme }) => ({
    display: "flex",
    flexDirection: "row",
    gap: theme.spacing(0.5),
}));

const CustomBox = styled("div")(({ theme }) => ({
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    width: theme.spacing(45.2),
    position: "relative",
}));

const CustomImageListItem = styled("div")(({ theme }) => ({
    display: "flex",
    width: theme.spacing(12.5),
    height: theme.spacing(12.5),
    padding: theme.spacing(1),
    borderRadius: theme.spacing(1.25),
    backgroundColor: "#bdbdbd",
    justifyContent: "center",
}));

const CustomImage = styled("img")(() => ({
    cursor: "pointer",
    width: "100%",
    height: "100%",
    objectFit: "cover",
}));

export default Carousel;