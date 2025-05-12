import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startPipeline } from "@/lib/pipeline";

export function useStartPipeline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pipelineName }: { pipelineName: string }) =>
      startPipeline(pipelineName),
    onSuccess: (data, variables) => {
      // Invalidate relevant queries to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ["pipeline", variables.pipelineName],
      });
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
  });
}
