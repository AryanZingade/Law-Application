import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import React from "react";

function Translate({
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
            onSelect={() => setTargetLanguage(lang.code)}
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

export default Translate;
