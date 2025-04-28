import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

function Verdict() {
  const [step, setStep] = useState(1);
  const [inputs, setInputs] = useState({
    caseDescription: "",
    jurisdiction: "",
    violation: "",
  });
  const [response, setResponse] = useState<any>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setInputs((prev) => ({ ...prev, [name]: value }));
  };

  const handleNext = () => setStep((prev) => prev + 1);

  const handleSubmit = async () => {
    // Simulate backend call
    const verdictResponse = {
      ...inputs,
      verdict: "Guilty",
      explanation:
        "The defendant violated the law as per the jurisdiction's rules.",
    };
    setResponse(verdictResponse);
  };

  const renderJson = (data: any) => {
    if (!data || typeof data !== "object") {
      return <p className="text-sm">{String(data)}</p>;
    }

    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="mb-3">
        <p className="font-medium">{key}:</p>
        {Array.isArray(value) ? (
          <ul className="ml-4 list-disc">
            {value.map((item, index) => (
              <li key={index}>
                {typeof item === "object" ? renderJson(item) : <p>{item}</p>}
              </li>
            ))}
          </ul>
        ) : typeof value === "object" ? (
          <div className="ml-4">{renderJson(value)}</div>
        ) : (
          <p>{String(value)}</p>
        )}
        <Separator className="my-2" />
      </div>
    ));
  };

  if (response) {
    return <div>{renderJson(response)}</div>;
  }

  return (
    <div className="space-y-4">
      {step === 1 && (
        <>
          <label className="block font-medium">Case Description</label>
          <textarea
            name="caseDescription"
            value={inputs.caseDescription}
            onChange={handleChange}
            className="w-full p-2 border rounded-md"
          />
          <Button onClick={handleNext}>Next</Button>
        </>
      )}

      {step === 2 && (
        <>
          <label className="block font-medium">Jurisdiction</label>
          <input
            type="text"
            name="jurisdiction"
            value={inputs.jurisdiction}
            onChange={handleChange}
            className="w-full p-2 border rounded-md"
          />
          <Button onClick={handleNext}>Next</Button>
        </>
      )}

      {step === 3 && (
        <>
          <label className="block font-medium">Violation</label>
          <input
            type="text"
            name="violation"
            value={inputs.violation}
            onChange={handleChange}
            className="w-full p-2 border rounded-md"
          />
          <Button onClick={handleSubmit}>Submit</Button>
        </>
      )}
    </div>
  );
}

export default Verdict;
