import { GlobalMutationProvider } from "@/lib/contexts/GlobalMutationProvider";
import { MessagesView } from "./MessagesView";
import { PromptInputBasic } from "./PromptInputBasic";

export function ChatSection() {
  return (
    <GlobalMutationProvider>
      <div className="flex h-svh w-full flex-col overflow-hidden p-4 items-center">
        <div className="w-full max-w-(--breakpoint-md) flex flex-col gap-4 items-center h-full">
          <MessagesView />
          <PromptInputBasic />
        </div>
      </div>
    </GlobalMutationProvider>
  );
}
