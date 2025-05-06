import { useMutation, useQueryClient } from "@tanstack/react-query";
import { stopPipeline } from "@/lib/pipeline";

export function useStopPipeline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pipelineName: string) => stopPipeline(pipelineName),
    onSuccess: (data, pipelineName) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["pipeline", pipelineName] });
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
  });
}
