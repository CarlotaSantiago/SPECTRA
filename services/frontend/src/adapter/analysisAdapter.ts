// src/adapters/configAdapter.ts
import { post } from "./xhr";
import type { DossierPayload } from "../types"

export const processState1 = (dossier: DossierPayload) => {
    return post("/process-state1", dossier);
}