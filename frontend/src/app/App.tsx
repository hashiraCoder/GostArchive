import React from "react";
import { AppShell } from "../components/AppShell";
import { ArchiveWorkspace } from "../components/ArchiveWorkspace";
import { ErrorBoundary } from "../components/ErrorBoundary";

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AppShell>
        <ArchiveWorkspace initialTab="overview" />
      </AppShell>
    </ErrorBoundary>
  );
};

export default App;
