import React from "react";
// @ts-ignore — type stubs may not be available yet
import { core } from "@apache-superset/core";
import ChatPage from "./ChatPage";
import ChatPanel from "./ChatPanel";

/**
 * Extension activation entrypoint called by Superset's extension loader.
 *
 * Registers:
 * 1. A dedicated "Ask Data" nav page accessible from the top navigation.
 * 2. Context-aware floating chat panels for Explore and Dashboard views.
 */
export const activate = (context: any) => {
  // 1. Dedicated full-page chat interface in the nav menu
  context.disposables.push(
    core.registerPage("mit.nl-explorer.page", {
      label: "Ask Data",
      icon: "ChatOutlined",
      component: ChatPage,
      path: "/nl-explorer",
    })
  );

  // 2. Floating panel injected into the Explore (chart builder) view
  context.disposables.push(
    core.registerViewProvider("mit.nl-explorer.explore-panel", (viewContext: any) => (
      <ChatPanel datasetId={viewContext?.datasource?.id} />
    ))
  );

  // 3. Floating panel injected into Dashboard views
  context.disposables.push(
    core.registerViewProvider("mit.nl-explorer.dashboard-panel", (viewContext: any) => (
      <ChatPanel dashboardId={viewContext?.dashboard?.id} />
    ))
  );

  console.log("[NL Explorer] Extension activated");
};

export const deactivate = () => {
  console.log("[NL Explorer] Extension deactivated");
};
