// LoadingCircle.tsx
import React from "react";

interface LoadingCircleProps {
  size?: string;
  color?: string;
}

const LoadingCircle: React.FC<LoadingCircleProps> = ({
  size = "50px",
  color = "blue",
}) => {
  return (
    <div
      style={{
        width: size,
        height: size,
        border: "6px solid #f3f3f3",
        borderTop: `6px solid ${color}`,
        borderRadius: "50%",
        animation: "spin 2s linear infinite",
      }}
    />
  );
};

export default LoadingCircle;
