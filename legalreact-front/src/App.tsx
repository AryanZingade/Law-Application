import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import TitleArea from "@/components/ui/TitleArea";
import TextInput from "@/components/ui/TextInput";
import PdfUpload from "./components/ui/PdfUpload";
import ResponseBox from "@/components/ui/ResponseBox"; // ✅ Import the new component

function App() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>("");
  const [documentReady, setDocumentReady] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null); // Store the uploaded file name

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      <div className="absolute top-4 left-4">
        <img
          src="/public/1631320061609.jpeg"
          alt="Logo"
          className="w-24 h-24"
        />
      </div>
      <TitleArea />
      {/* Text input area */}
      <TextInput setResponse={setResponse} />
      {/* Upload section for PDF summarize/translate */}
      <PdfUpload
        setResponse={setResponse}
        setUploadedFileName={setUploadedFileName} // Pass function to handle uploaded file name
        setDocumentReady={setDocumentReady}
      />
      {/* Display response */}
      {response && <ResponseBox response={response} />}{" "}
      {/* ✅ Shadcn version */}
    </div>
  );
}

export default App;
