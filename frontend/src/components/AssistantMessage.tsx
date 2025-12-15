import { Markdown } from "@/components/prompt-kit/markdown";
import { Message, MessageAvatar } from "@/components/prompt-kit/message";
import { TMessage } from "@/lib/types/message";

export function AssistantMessage({ message }: { message: TMessage }) {
  return (
    <Message className="justify-start">
      <MessageAvatar src="/avatars/ai.png" alt="AI Assistant" fallback="AI" />
      <div className="max-w-[85%] flex-1 sm:max-w-[75%]">
        <div className="bg-secondary text-foreground prose rounded-lg p-2">
          <Markdown>{message.content}</Markdown>
        </div>
      </div>
    </Message>
  );
}
