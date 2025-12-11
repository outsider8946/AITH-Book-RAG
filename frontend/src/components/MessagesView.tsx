"use client";

import {
  ChatContainerContent,
  ChatContainerRoot,
} from "@/components/prompt-kit/chat-container";
import { AssistantMessage } from "@/components/AssistantMessage";
import { UserMessage } from "@/components/UserMessage";
import { useGetMessagesQuery } from "@/lib/queries/useGetMessagesQuery";
import { useGlobalMutation } from "@/lib/contexts/mutationContext";
import { Loader } from "./prompt-kit/loader";
import { SystemMessage } from "./prompt-kit/system-message";

export function MessagesView() {
  const { variables, isPending, error } = useGlobalMutation();
  const { data: messages } = useGetMessagesQuery();

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      <ChatContainerRoot className="flex-1">
        <ChatContainerContent className="space-y-4 p-4">
          {messages?.map((message) =>
            message.role === "assistant" ? (
              <AssistantMessage key={message.id} message={message} />
            ) : (
              <UserMessage key={message.id} content={message.content} />
            )
          )}
          {(isPending || error !== null) && <UserMessage content={variables} />}
          {isPending && <Loader variant="dots" />}
          {error !== null && (
            <SystemMessage variant="error" fill>
              {(error as Error).message}
            </SystemMessage>
          )}
        </ChatContainerContent>
      </ChatContainerRoot>
    </div>
  );
}
