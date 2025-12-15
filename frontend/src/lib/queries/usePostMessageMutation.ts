import { useMutation } from "@tanstack/react-query";
import { postMessage } from "@/lib/api/postMessage";
import { queryClient } from "@/lib/queryClient/queryClient";

export const usePostMessageMutation = () =>
  useMutation({
    mutationKey: ["addMessage"],
    mutationFn: (message: string) => postMessage(message),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["messages"] }),
  });
