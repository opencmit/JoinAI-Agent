"use client";

import React, { createContext, useContext, ReactNode } from "react";
import { AgentState, defaultAgentState } from "@/types/agent";


// 定义 AgentContext 的值类型
export type AgentContextType = {
  sandboxId: string | null;
  agentState: AgentState;
  setAgentState: (newState: AgentState | ((prevState: AgentState | undefined) => AgentState)) => void;
}

// 创建 AgentContext，传递完整的 agent state
const AgentContext = createContext<AgentContextType>({
  sandboxId: null,
  agentState: defaultAgentState,
  setAgentState: () => { }
});

// 导出 hook 供子组件使用
export function useSandboxContext() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error("useSandboxContext 必须在 AgentProvider 内部使用");
  }
  return context;
}

export function useAgentContext() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error("useAgentContext 必须在 AgentProvider 内部使用");
  }
  return context;
}

// AgentProvider 组件
export const AgentProvider: React.FC<{ children: ReactNode, value: AgentContextType }> = ({ children, value }: { children: ReactNode, value: AgentContextType }) => {
  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
};