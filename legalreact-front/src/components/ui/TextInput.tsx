"use client";

import React, { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input"; // Import your custom Input

interface TextInputProps {
  setResponse: (data: any) => void;
}

function TextInput({ setResponse }: TextInputProps) {
  const [query, setQuery] = useState("");

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const sendQuery = async () => {
    if (!query.trim()) return;
    try {
      const res = await axios.post("http://127.0.0.1:5000/invoke", {
        user_input: query,
      });
      setResponse(res.data);
    } catch (error) {
      console.error("Error sending query:", error);
      setResponse("Error fetching response.");
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4 w-full max-w-xl">
      <Input
        type="text"
        placeholder="Enter your legal query"
        value={query}
        onChange={handleQueryChange}
        onKeyDown={(e) => e.key === "Enter" && sendQuery()}
        className="text-base"
      />
      <Button onClick={sendQuery}>Send</Button>
    </div>
  );
}

export default TextInput;
