import { BrowserUseSteps } from "./browser-use";

export interface UsageMetadata {
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
    time_to_first_token?: number;
    total_response_time?: number;
    generation_time?: number;
}

export type AGENT_TYPE = "normal";

export type AGENT_STATUS = "idle" | "running" | "canceled";

// 定义 AgentState 类型
export type AgentState = {
    status: AGENT_STATUS;
    e2b_sandbox_id: string;
    copilotkit: { actions: any[] };
    messages: any[];
    logs: any[];
    plan: {
        thought: string;
        title: string;
        steps: {
            agent_name: string;
            description: string;
            note: string;
            step_index: number;
        }[];
    };
    current_plan_step: number;
    structure_tool_results: Record<string, Record<string, any>>;
    mcp_tool_execution_results: any[];
    mode: string;
    agent_type: AGENT_TYPE;
    usage_metadata: Record<string, UsageMetadata>;
    inner_messages?: any[];
    files: string[];
    browser_use_steps: BrowserUseSteps | null;
};

// 默认的 AgentState
export const defaultAgentState: AgentState = {
    status: 'idle',
    e2b_sandbox_id: "",
    copilotkit: { actions: [] },
    messages: [],
    logs: [],
    plan: {
        thought: "",
        title: "",
        steps: [],
    },
    current_plan_step: 1,
    structure_tool_results: {},
    mode: "",
    agent_type: "normal",
    usage_metadata: {},
    files: [],
    mcp_tool_execution_results: [],
    browser_use_steps: null
};

export const defaultMetaData = {
    title: "",
    assistantId: "",
    top: false,
    attachmentList: [],
    agentType: 'normal',
}