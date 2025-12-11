import { Message, MessageContent } from "@/components/prompt-kit/message";

export function UserMessage({ content }: { content: string }) {
  return (
    <Message className="justify-end">
      <div className="max-w-[85%] flex-1 sm:max-w-[75%]">
        <MessageContent className="bg-primary text-primary-foreground">
          {content}
        </MessageContent>
      </div>
    </Message>
  );
}
