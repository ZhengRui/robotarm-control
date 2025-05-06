import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { getPipelines } from "@/lib/pipeline";
import { pipelinesAtom } from "@/atoms";
import { PipelinesResponse } from "@/interfaces";

export function useGetPipelines(withMeta = false) {
  const [, setPipelines] = useAtom(pipelinesAtom);

  const result = useQuery<PipelinesResponse>({
    queryKey: ["pipelines", withMeta],
    queryFn: () => getPipelines(withMeta) as Promise<PipelinesResponse>,
    staleTime: 30000, // Data stays fresh for 30 seconds
  });

  // Update pipelines atom when data is available
  if (result.data) {
    setPipelines(result.data.pipelines);
  }

  return result;
}
