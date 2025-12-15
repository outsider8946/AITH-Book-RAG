import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { getMessages } from "@/lib/api/getMessages";
import type { TMessage } from "@/lib/types/message";

export const useGetMessagesQuery = (): UseQueryResult<TMessage[]> => {
  return useQuery({
    queryKey: ["messages"],
    queryFn: () => getMessages(),
    retry: false,
  });
};
