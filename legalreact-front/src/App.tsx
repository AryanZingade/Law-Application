import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import TitleArea from "@/components/ui/TitleArea";
import TextInput from "@/components/ui/TextInput";
import PdfUpload from "./components/ui/PdfUpload";
import Translate from "./components/ui/TranslateDropdown";
import ResponseBox from "@/components/ui/ResponseBox"; // ✅ Import the new component

function App() {
  const [response, setResponse] = useState<any>("");
  const [documentReady, setDocumentReady] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState("en");

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      <TitleArea />
      {/* Text input area */}
      <TextInput setResponse={setResponse} />
      {/* Language selection dropdown */}
      <div className="my-4">
        <Translate
          targetLanguage={targetLanguage}
          setTargetLanguage={setTargetLanguage}
        />
      </div>
      {/* Upload section for PDF summarize/translate */}
      <PdfUpload
        setResponse={setResponse}
        targetLanguage={targetLanguage}
        setDocumentReady={setDocumentReady}
      />
      {/* Display response */}
      {response && <ResponseBox response={response} />}{" "}
      {/* ✅ Shadcn version */}
    </div>
  );
}

export default App;
