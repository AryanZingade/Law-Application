import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";
import axios from "axios";
import { FaFolder, FaGlobe } from "react-icons/fa";

function PdfUpload({
  setResponse,
  targetLanguage,
  setDocumentReady,
}: {
  setResponse: (data: any) => void;
  targetLanguage: string;
  setDocumentReady: (ready: boolean) => void;
}) {
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
    type: "summarize" | "translate"
  ) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      console.log("Selected File:", selectedFile);
      const formData = new FormData();
      formData.append("file", selectedFile);

      if (type === "translate") {
        formData.append("target_language", targetLanguage);
      }

      const route = type === "summarize" ? "summarize" : "translatedoc";

      setIsUploading(true);
      try {
        const response = await axios.post(
          `http://127.0.0.1:5000/${route}`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        setResponse(response.data);
        setDocumentReady(true);
      } catch (error) {
        console.error(`Error uploading file to ${route}:`, error);
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <TooltipProvider>
      <div className="flex gap-4 mt-4">
        {/* Summarize Upload */}
        <Tooltip>
          <div>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => handleUpload(e, "summarize")}
              style={{ display: "none" }}
              id="summarize-file"
            />
            <label htmlFor="summarize-file">
              <Button
                asChild
                variant="outline"
                disabled={isUploading}
                className="rounded-full flex items-center justify-center cursor-pointer"
              >
                <span>
                  <FaFolder className="mr-2" size={20} />
                  {isUploading ? "Uploading..." : "Summarize"}
                </span>
              </Button>
            </label>
            <TooltipContent>Upload PDF to Summarize</TooltipContent>
          </div>
        </Tooltip>

        {/* Translate Upload */}
        <Tooltip>
          <div>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => handleUpload(e, "translate")}
              style={{ display: "none" }}
              id="translate-file"
            />
            <label htmlFor="translate-file">
              <Button
                asChild
                variant="outline"
                disabled={isUploading}
                className="rounded-full flex items-center justify-center cursor-pointer"
              >
                <span>
                  <FaGlobe className="mr-2" size={20} />
                  {isUploading ? "Uploading..." : "Translate"}
                </span>
              </Button>
            </label>
            <TooltipContent>Upload PDF to Translate</TooltipContent>
          </div>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

export default PdfUpload;
