"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";

interface PdfUploadProps {
  setResponse: (data: any) => void;
  setUploadedFileName: (fileName: string) => void;
  setDocumentReady: (ready: boolean) => void;
}

function PdfUpload({
  setResponse,
  setUploadedFileName,
  setDocumentReady,
}: PdfUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setLocalFileName] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      alert("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    try {
      const uploadRes = await axios.post(
        "http://127.0.0.1:5000/upload-pdf",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      const filename = uploadRes.data.filename;
      setUploadedFileName(filename);
      setLocalFileName(filename);
      setDocumentReady(true);

      alert("File uploaded successfully!");

      // After upload, trigger invoke
      await sendQuery(`#UPLOAD_PDF\nFilename: ${filename}`);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Check console for details.");
    } finally {
      setIsUploading(false);
    }
  };

  const sendQuery = async (user_input: string) => {
    try {
      const res = await axios.post("http://127.0.0.1:5000/invoke", {
        user_input,
      });
      setResponse(res.data);
    } catch (error) {
      console.error("Error while invoking:", error);
      setResponse("Error fetching response after upload.");
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
