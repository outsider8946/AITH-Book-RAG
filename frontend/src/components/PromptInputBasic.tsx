"use client";

import {
  PromptInput,
  PromptInputAction,
  PromptInputActions,
  PromptInputTextarea,
} from "@/components/prompt-kit/prompt-input";
import { Button } from "@/components/ui/button";
import { useGlobalMutation } from "@/lib/contexts/mutationContext";
import { ArrowUp, Square } from "lucide-react";
import { useState } from "react";

export function PromptInputBasic() {
  const { mutate: postMessage, isPending } = useGlobalMutation();

  const [input, setInput] = useState("");
  const handleSubmit = () => {
    postMessage(input);
    setInput("");
  };

  const handleValueChange = (value: string) => {
    setInput(value);
  };

  return (
    <PromptInput
      value={input}
      onValueChange={handleValueChange}
      isLoading={isPending}
      onSubmit={handleSubmit}
      className="w-full max-w-(--breakpoint-md)"
      disabled={isPending}
    >
      <PromptInputTextarea placeholder="Ask me anything..." />
      <PromptInputActions className="justify-end pt-2">
        <PromptInputAction
          tooltip={isPending ? "Stop generation" : "Send message"}
        >
          <Button
            variant="default"
            size="icon"
            className="h-8 w-8 rounded-full"
            onClick={handleSubmit}
          >
            {isPending ? (
              <Square className="size-5 fill-current" />
            ) : (
              <ArrowUp className="size-5" />
            )}
          </Button>
        </PromptInputAction>
      </PromptInputActions>
    </PromptInput>
  );
}
