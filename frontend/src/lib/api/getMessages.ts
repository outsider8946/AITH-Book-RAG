import axios from "axios";
import { TMessage } from "../types/message";

export const getMessages = async (): Promise<TMessage[]> =>
  (await axios.get<TMessage[]>("/api/messages")).data;
