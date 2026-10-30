import React from "react";
import { AppShell } from "../components/AppShell";
import { ArchiveWorkspace } from "../components/ArchiveWorkspace";

export const App: React.FC = () => {
  return (
    <AppShell>
      <ArchiveWorkspace />
    </AppShell>
  );
};

export default App;
