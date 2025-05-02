import { atom } from "jotai";

// Pipeline state atoms
export const selectedPipelineAtom = atom<string | null>("YahboomPickAndPlace");
export const pipelineRunningAtom = atom<boolean>(false);
export const currentStatusAtom = atom<string>("PICKING");

// Signal and queue state atoms
export const selectedSignalAtom = atom<string | null>(null);
export const selectedQueueAtom = atom<string | null>(null);

// Data atoms
export const availablePipelinesAtom = atom<string[]>([
  "YahboomPickAndPlace",
  "OtherPipeline",
]);

export const pipelineStatusesAtom = atom<string[]>([
  "IDLE",
  "RUNNING",
  "CALIBRATING",
  "PICKING",
  "PLACING",
]);

export const pipelineSignalsAtom = atom<string[]>([
  "STOP",
  "PAUSE",
  "RESUME",
  "RESET",
  "CALIBRATE",
]);

export const pipelineQueuesAtom = atom<string[]>([
  "CAMERA",
  "PROCESS",
  "DETECTION",
  "ARM_STATE",
  "ROBOT_CONTROL",
]);

// Layout state atoms
export const isMobileAtom = atom<boolean>(false);
