import type { UseMutationResult } from "@tanstack/react-query";
import { createContext, useContext } from "react";
import type { TMessage } from "@/lib/types/message";

export const MutationContext = createContext<UseMutationResult<
  TMessage,
  Error,
  string
> | null>(null);

export const useGlobalMutation = () => {
  const ctx = useContext(MutationContext);
  if (!ctx) {
    throw new Error(
      "useGlobalMutation must be used within GlobalMutationProvider"
    );
  }
  return ctx;
};
