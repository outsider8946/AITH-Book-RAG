import { type ReactNode } from "react";
import { MutationContext } from "./mutationContext";
import { usePostMessageMutation } from "@/lib/queries/usePostMessageMutation";

export const GlobalMutationProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const mutation = usePostMessageMutation();

  return (
    <MutationContext.Provider value={mutation}>
      {children}
    </MutationContext.Provider>
  );
};
