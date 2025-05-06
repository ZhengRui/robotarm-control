import { useMutation } from "@tanstack/react-query";
import { sendSignal } from "@/lib/pipeline";

export function useSendSignal() {
  return useMutation({
    mutationFn: ({
      pipelineName,
      signalName,
      priority = "NORMAL",
    }: {
      pipelineName: string;
      signalName: string;
      priority?: string;
    }) => sendSignal(pipelineName, signalName, priority),
  });
}
