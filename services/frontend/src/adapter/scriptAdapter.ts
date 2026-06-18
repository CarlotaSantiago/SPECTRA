import { post } from "./xhr";
import type { GeneratePayload } from "../types";

export const editScript = async (payload: GeneratePayload) => {
    return post("/process-state2", payload);
}