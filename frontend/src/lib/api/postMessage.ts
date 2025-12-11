import axios from "axios";
import type { TMessage } from "@/lib/types/message";

export const postMessage = async (message: string): Promise<TMessage> =>
  (await axios.post<TMessage>("/api/messages", message)).data;
