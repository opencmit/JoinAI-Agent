import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
    langGraphPlatformEndpoint
} from "@noahlocal/copilotkit-runtime";
import { NextRequest } from "next/server";

// You can use any service adapter here for multi-agent support.
const serviceAdapter = new ExperimentalEmptyAdapter();

export const POST = async (req: NextRequest) => {
    const userId = req.url.split('?')[1].split('=')[1];

    const runtime = new CopilotRuntime({
        remoteEndpoints: [
            langGraphPlatformEndpoint({
                deploymentUrl: process.env.LANGGRAPH_URL!, // make sure to replace with your real deployment url,
                langsmithApiKey: process.env.LANGSMITH_API_KEY, // only used in LangGraph Platform deployments
                agents: [ // List any agents available under "graphs" list in your langgraph.json file; give each a description explaining when it should be called.
                    {
                        name: 'agent',
                        description: 'A helpful LLM agent.',
                        assistantId: userId // 用userId的值
                    }
                ]
            }),
        ],
    });

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter,
        endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
};