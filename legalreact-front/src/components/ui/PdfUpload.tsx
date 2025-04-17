import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";

function PdfUpload({
  setResponse,
  setUploadedFileName, // New prop for updating uploaded file name
  setDocumentReady,
}: {
  setResponse: (data: any) => void;
  setUploadedFileName: (fileName: string) => void; // Type the function properly
  setDocumentReady: (ready: boolean) => void;
}) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setLocalFileName] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      return alert("Please select a PDF file.");
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/upload-pdf",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      const filename = response.data.filename; // Assuming backend sends filename
      setUploadedFileName(filename); // Update the global state with the file name
      setLocalFileName(filename); // Local state for the file name

      alert("File uploaded successfully!");
      setDocumentReady(true); // Notify that document is ready
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Check console for details.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="mt-4">
      <label htmlFor="file-upload">
        <Button
          asChild
          variant="outline"
          disabled={isUploading}
          className="rounded-full flex items-center justify-center cursor-pointer"
        >
          <span>
            <FaFilePdf className="mr-2" size={20} />
            {isUploading ? "Uploading..." : "Upload PDF"}
          </span>
        </Button>
        <Input
          id="file-upload"
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          className="hidden"
        />
      </label>

      {uploadedFileName && (
        <div className="mt-4">
          <span>Uploaded File: {uploadedFileName}</span>
        </div>
      )}
    </div>
  );
}

export default PdfUpload;
