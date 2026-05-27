import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { LogsProvider } from "@/contexts/LogsContext";
import ManualMode from "./pages/ManualMode";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

const App = () => (
  <LogsProvider>
    <Toaster position="top-right" richColors />
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/manual-mode" element={<ManualMode />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  </LogsProvider>
);

export default App;
