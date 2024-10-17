import React, { useRef, useState, useEffect } from "react";
import { IconButton } from "@mui/material";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import FullscreenExitIcon from "@mui/icons-material/FullscreenExit";
import { styled } from "@mui/material/styles";


/**
 * ImageVisualization component displays an image with fullscreen option.
 * @param {string} props.imagePath - Path to the image to be displayed.
 * @returns {JSX.Element} Component for displaying an image with fullscreen option.
 */
const ImageVisualization = ({ imagePath }) => {
    const containerRef = useRef(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    
    // Event listener to detect fullscreen changes
    useEffect(() => {
        function handleFullscreenChange() {
        setIsFullscreen(document.fullscreenElement !== null);
        }
        document.addEventListener("fullscreenchange", handleFullscreenChange);
        return () => {
        document.removeEventListener("fullscreenchange", handleFullscreenChange);
        };
    }, []);

    // Function to request fullscreen mode
    const handleFullscreenClick = () => {
        containerRef.current.requestFullscreen();
    };
    // Function to exit fullscreen mode
    const handleExitFullscreenClick = () => {
        document.exitFullscreen();
    };
    
    return (
        <CustomDiv ref={containerRef}>
        {/* Image to be displayed */}
        <CustomImg src={imagePath} alt="Artifact" />
        <div>
            {/* Fullscreen buttons */}
            {isFullscreen ? (
                <CustomIconButton onClick={handleExitFullscreenClick}>
                    <FullscreenExitIcon />
                </CustomIconButton>
            ) : (
                <CustomIconButton onClick={handleFullscreenClick}>
                    <FullscreenIcon />
                </CustomIconButton>
            )}
        </div>
        </CustomDiv>
    );
}

// Styled components for custom styling
const CustomDiv = styled("div")(({ theme }) => ({
    width: "100%",
    height: theme.spacing(75),
    position: "relative",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "black",
    overflow: "hidden",
}));

const CustomImg = styled("img")(() => ({
    width: "100%",
    height: "100%",
    objectFit: "contain",
}));

const CustomIconButton = styled(IconButton)({
    color: "white",
    position: "absolute",
    zIndex: 1,
    top: 10,
    right: 10,
});

export default ImageVisualization;