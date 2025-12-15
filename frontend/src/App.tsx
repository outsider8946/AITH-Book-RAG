import { Toaster } from "sonner";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient/queryClient";
import { ChatSection } from "./components/ChatSection";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatSection />
      <Toaster richColors />
    </QueryClientProvider>
  );
}

export default App;
