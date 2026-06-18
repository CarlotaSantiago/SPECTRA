import { post } from "./xhr";
import type { GeneratePayload } from "../types";

export const generateScript = async (payload: GeneratePayload) => {
    return post("/process-state2", payload);
}