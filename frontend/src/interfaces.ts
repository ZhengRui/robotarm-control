/**
 * Interface for the Pipeline data structure from the backend
 */
export interface Pipeline {
  name: string;
  config: Record<string, any>;
  queues: string[];
  running: boolean;
  state: string;
  timestamp: number;
  available_states: string[];
  available_signals: string[];
  available_queues: string[];
  config_schema: Record<string, any>;
}

/**
 * Response structure for the getPipelines API
 */
export interface PipelinesResponse {
  pipelines: Pipeline[];
}
