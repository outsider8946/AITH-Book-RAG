export type TMessage = {
  id: number | string;
  role: "user" | "assistant";
  content: string;
};
