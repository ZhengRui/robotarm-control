import { atom } from "jotai";
import { Pipeline } from "./interfaces";

// Core atoms - minimal set needed
export const pipelinesAtom = atom<Pipeline[]>([]);
export const selectedPipelineNameAtom = atom<string | null>(null);
export const selectedSignalAtom = atom<string | null>(null);

// UI state
export const isMobileAtom = atom<boolean>(false);
