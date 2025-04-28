import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

type ResponseBoxProps = {
  response: any;
  loading?: boolean;
};

function ResponseBox({ response }: ResponseBoxProps) {
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

  return (
    <Card className="w-full max-w-4xl mt-6 bg-muted shadow-md border">
      <CardContent className="p-4">
        <h3 className="text-lg font-semibold mb-4">Response from Flask:</h3>
        <ScrollArea className="h-[350px] w-full pr-2">
          {typeof response === "object" ? (
            <div>{renderJson(response)}</div>
          ) : (
            <p>{String(response)}</p>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export default ResponseBox;
