import { requestTemplate, responseHandlerTemplate } from "./requestTemplate";

const apiEndpoint = process.env.NEXT_PUBLIC_API_ENDPOINT || "";

// API Endpoints
export const getPipelines = requestTemplate(
  (withMeta: boolean = false) => ({
    url: `${apiEndpoint}/pipelines?with_meta=${withMeta}`,
    method: "GET",
    headers: new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    }),
  }),
  responseHandlerTemplate
);

export const getPipeline = requestTemplate(
  (pipelineName: string, withMeta: boolean = false) => ({
    url: `${apiEndpoint}/pipeline?pipeline_name=${pipelineName}&with_meta=${withMeta}`,
    method: "GET",
    headers: new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    }),
  }),
  responseHandlerTemplate
);

export const startPipeline = requestTemplate(
  (pipelineName: string, debug: boolean = false) => ({
    url: `${apiEndpoint}/pipeline/start?pipeline_name=${pipelineName}&debug=${debug}`,
    method: "POST",
    headers: new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    }),
  }),
  responseHandlerTemplate
);

export const stopPipeline = requestTemplate(
  (pipelineName: string) => ({
    url: `${apiEndpoint}/pipeline/stop?pipeline_name=${pipelineName}`,
    method: "POST",
    headers: new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    }),
  }),
  responseHandlerTemplate
);

export const sendSignal = requestTemplate(
  (pipelineName: string, signalName: string, priority: string = "NORMAL") => ({
    url: `${apiEndpoint}/pipeline/signal?pipeline_name=${pipelineName}&signal_name=${signalName}&priority=${priority}`,
    method: "POST",
    headers: new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    }),
  }),
  responseHandlerTemplate
);

// WebSocket connections
export const createPipelineWebSocket = (pipelineName: string) => {
  const wsEndpoint = apiEndpoint.replace(/^http/, "ws");
  return new WebSocket(
    `${wsEndpoint}/ws/pipeline?pipeline_name=${pipelineName}`
  );
};

export const createQueueWebSocket = (
  pipelineName: string,
  queueName: string
) => {
  const wsEndpoint = apiEndpoint.replace(/^http/, "ws");
  return new WebSocket(
    `${wsEndpoint}/ws/queue?pipeline_name=${pipelineName}&queue_name=${queueName}`
  );
};
