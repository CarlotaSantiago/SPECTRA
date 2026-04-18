// src/adapters/configAdapter.ts
import { post } from "./xhr";
import type { DossierPayload } from "../feature/types"

export const processState1 = async (dossier: DossierPayload) => {
    const res = await post("/process-state1", dossier);
    return res.data;
}