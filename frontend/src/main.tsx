import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./register/tokens.css";
import "./register/base.css";
import "./register/app.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
