import { useQuery } from "@tanstack/react-query";
import { getPipeline } from "@/lib/pipeline";
import { Pipeline } from "@/interfaces";

export function useGetPipeline(pipelineName: string | null, withMeta = false) {
  return useQuery<Pipeline>({
    queryKey: ["pipeline", pipelineName, withMeta],
    queryFn: () => getPipeline(pipelineName!, withMeta) as Promise<Pipeline>,
    enabled: !!pipelineName, // Only run query if pipelineName exists
    staleTime: 5000, // Data stays fresh for 5 seconds
  });
}
