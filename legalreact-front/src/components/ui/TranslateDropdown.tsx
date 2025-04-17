import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import React from "react";

function TranslateDropdown({
  targetLanguage,
  setTargetLanguage,
}: {
  targetLanguage: string;
  setTargetLanguage: (lang: string) => void;
}) {
  const languages = [
    { code: "en", label: "English" },
    { code: "hi", label: "Hindi" },
    // Add more languages as needed
  ];

  const selectedLabel =
    languages.find((l) => l.code === targetLanguage)?.label ||
    "Select Language";

  const handleLanguageSelect = async (langCode: string) => {
    setTargetLanguage(langCode);

    try {
      const response = await fetch("/invoke", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ targetLanguage: langCode }),
      });

      const data = await response.json();
      console.log("Server response:", data);
    } catch (error) {
      console.error("Error sending language to server:", error);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="w-48">
          {selectedLabel}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-48">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onSelect={() => handleLanguageSelect(lang.code)}
            className={
              targetLanguage === lang.code ? "font-medium bg-muted" : ""
            }
          >
            {lang.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default TranslateDropdown;
