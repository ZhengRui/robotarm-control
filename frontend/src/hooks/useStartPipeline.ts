import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startPipeline } from "@/lib/pipeline";

export function useStartPipeline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      pipelineName,
      debug = false,
    }: {
      pipelineName: string;
      debug?: boolean;
    }) => startPipeline(pipelineName, debug),
    onSuccess: (data, variables) => {
      // Invalidate relevant queries to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ["pipeline", variables.pipelineName],
      });
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
  });
}
