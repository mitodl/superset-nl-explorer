import React from "react";
import { createRoot } from "react-dom/client";
import ChatPage from "./ChatPage";

const container = document.getElementById("root");
if (container) {
  createRoot(container).render(
    <React.StrictMode>
      <ChatPage />
    </React.StrictMode>
  );
}
