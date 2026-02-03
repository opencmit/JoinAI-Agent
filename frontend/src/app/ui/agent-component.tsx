"use client"

import { useCoAgent } from "@noahlocal/copilotkit-react-core";
import { AgentState, defaultAgentState, AGENT_TYPE } from "@/types/agent";
import { AgentProvider } from "@/lib/agent-context";
import { useMessageContext } from "@/lib/message-context";

import { CASE_MESSAGE } from "@/cases";

export function AgentComponent({ children, caseId }: { children: React.ReactNode, caseId: string }) {

    const initialState = defaultAgentState;

    const { getAgentInfo } = useMessageContext();


    if (caseId) {
        const caseData = CASE_MESSAGE[caseId as keyof typeof CASE_MESSAGE];
        initialState.e2b_sandbox_id = "debug_sandbox_id";

        const configItem = caseData[0];
        if (configItem && 'state' in configItem) {
            initialState.agent_type = configItem.state!.agent_type as AGENT_TYPE;
        }
    } else {
        initialState.agent_type = getAgentInfo().agentType as AGENT_TYPE;
    }

    const agentConfig = {
        name: "agent",
        initialState,
        config: {
            configurable: {},
            recursion_limit: 50,
        },
    };

    const { state, setState } = useCoAgent<AgentState>(agentConfig);

    return (
        <AgentProvider value={{
            sandboxId: state.e2b_sandbox_id,
            agentState: state,
            setAgentState: setState
        }}>
            {children}
        </AgentProvider>
    );
} 