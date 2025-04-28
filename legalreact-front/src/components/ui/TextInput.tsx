"use client";

import React, { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface TextInputProps {
  setResponse: (data: any) => void;
}

function TextInput({ setResponse }: TextInputProps) {
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState<
    "default" | "jurisdiction" | "violation" | "facts" | "complete"
  >("default");

  const [jurisdiction, setJurisdiction] = useState("");
  const [violation, setViolation] = useState("");
  const [facts, setFacts] = useState("");

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleMainSubmit = () => {
    if (!query.trim()) return;
    if (query.toLowerCase().includes("verdict")) {
      setStage("jurisdiction");
    } else {
      sendQuery(query);
    }
  };

  const sendQuery = async (user_input: string) => {
    try {
      const res = await axios.post("http://127.0.0.1:5000/invoke", {
        user_input,
      });
      setResponse(res.data);
    } catch (error) {
      console.error("Error:", error);
      setResponse("Error fetching response.");
    }
  };

  const handleJurisdictionSubmit = () => {
    if (!jurisdiction.trim()) return;
    setStage("violation");
  };

  const handleViolationSubmit = () => {
    if (!violation.trim()) return;
    setStage("facts");
  };

  const handleFactsSubmit = () => {
    if (!facts.trim()) return;
    setStage("complete");
  };

  const handleFinalSubmit = () => {
    const finalPrompt = `#VERDICT\nJurisdiction: ${jurisdiction}\nViolation: ${violation}\nFacts: ${facts}`;
    sendQuery(finalPrompt);
  };

  return (
    <div className="flex flex-col gap-4 w-full max-w-xl">
      <div className="flex flex-row gap-4">
        <Input
          type="text"
          placeholder="Enter your legal query"
          value={query}
          onChange={handleQueryChange}
          onKeyDown={(e) => e.key === "Enter" && handleMainSubmit()}
        />
        <Button onClick={handleMainSubmit}>Send</Button>
      </div>

      {/* Progressive Input Stages */}
      {stage === "jurisdiction" && (
        <div className="flex flex-row gap-4">
          <Input
            placeholder="Jurisdiction"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleJurisdictionSubmit()}
          />
          <Button onClick={handleJurisdictionSubmit}>Next</Button>
        </div>
      )}

      {stage === "violation" && (
        <div className="flex flex-row gap-4">
          <Input
            placeholder="Violation of Law"
            value={violation}
            onChange={(e) => setViolation(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleViolationSubmit()}
          />
          <Button onClick={handleViolationSubmit}>Next</Button>
        </div>
      )}

      {stage === "facts" && (
        <div className="flex flex-row gap-4">
          <Input
            placeholder="Facts"
            value={facts}
            onChange={(e) => setFacts(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleFactsSubmit()}
          />
          <Button onClick={handleFactsSubmit}>Next</Button>
        </div>
      )}

      {stage === "complete" && (
        <div className="flex justify-center">
          <Button onClick={handleFinalSubmit} className="w-fit">
            Submit Verdict Query
          </Button>
        </div>
      )}
    </div>
  );
}

export default TextInput;
