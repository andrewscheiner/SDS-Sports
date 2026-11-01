import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import NflDashboard from "@/pages/NflDashboard";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/sports/nfl" element={<NflDashboard />} />
        <Route path="*" element={<Navigate to="/sports/nfl" replace />} />
      </Routes>
      <Toaster theme="dark" position="bottom-right" />
    </BrowserRouter>
  );
}

export default App;
