"use server"

import { Thread, DefaultValues, Run } from "@langchain/langgraph-sdk";

import { CopilotKit } from "@noahlocal/copilotkit-react-core";
import { AgentComponent } from "@/app/ui/agent-component";
import { getAssistant, createAssistant, updateAssistant, getThread, getThreadRuns } from "@/lib/langgraph-client";

import { Chat } from "@/app/ui/chat";

import { HomePage } from "@/app/ui/home-page";

import { formatDate } from "@/utils/date";

// import { sm2 } from "sm-crypto";

export default async function Home({
    searchParams,
}: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
    console.log('加载chat page')

    const userId = "12345678-1234-1234-1234-123456789012"
    const userName = "test-name"
    const orgId = "test-org"

    if (userId) {
        getAssistant(userId || "")
            .then((assistant) => {
                console.log('getAssistant success', userId, assistant)
                if (assistant) {
                    updateAssistant(userId, { name: userName, description: "聚智工坊", metadata: { userId, userName, orgId, channel: "聚智工坊", lastLoginTime: formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss') } })
                        .then((assistants) => {
                            console.log('updateAssistant success', userId, assistants)
                        }).catch((error) => {
                            console.error('updateAssistant fail', userId, error)
                        })
                } else {
                    createAssistant({ graphId: "agent", assistantId: userId, name: userName, description: "聚智工坊", ifExists: "do_nothing", metadata: { userId, userName, orgId, channel: "聚智工坊", lastLoginTime: formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss') } })
                        .then((assistants) => {
                            console.log('createAssistant success', userId, assistants)
                        }).catch((error) => {
                            console.error('createAssistant fail', userId, error)
                        })
                }
            }).catch((error) => {
                console.error('getAssistant fail', userId, error)
                createAssistant({ graphId: "agent", assistantId: userId, name: userName, description: "聚智工坊", ifExists: "do_nothing", metadata: { userId, userName, orgId, channel: "聚智工坊", lastLoginTime: formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss') } })
                    .then((assistants) => {
                        console.log('createAssistant success', userId, assistants)
                    }).catch((error) => {
                        console.error('createAssistant fail', userId, error)
                    })
            })
    } else {
        console.log('无userId, 进入loading页面')
        return null;
    }

    const { threadId = "", init = "false", caseId = "" } = await searchParams

    if (caseId) {
        return (
            <div className="w-full h-screen overflow-y-hidden custom-scrollbar">
                <CopilotKit
                    runtimeUrl={`/api/copilotkit?userId=${userId}`}
                    agent="agent" // the name of the agent you want to use
                >
                    <AgentComponent caseId={caseId as string}>
                        <Chat
                            threadId=""
                            threadStatus="idle"
                            caseId={caseId as string}
                        />
                    </AgentComponent>
                </CopilotKit>
            </div>
        )
    }

    let isInit: boolean = true;
    let runs: Run[] | null = null;
    let thread: Thread<DefaultValues> | null = null;
    if (threadId == "") {
        console.log("无threadId, 进入loading页面")
    } else {
        console.log("有threadId, 无message", threadId)
        runs = await getThreadRuns(threadId as string);
        thread = await getThread(threadId as string);
        if (runs && runs.length > 0 || init == "true") {
            console.log("有threadId, 无message, 有values, 进入chat页面")
            isInit = false;
        } else {
            console.log("有threadId, 无message, 无values, 进入home页面")
            isInit = true;
        }
    }

    // 生成SM2密钥对
    // let keypair = sm2.generateKeyPairHex();
    // console.log('keypair', keypair)

    return (
        <div className="w-full h-screen overflow-y-hidden custom-scrollbar">
            {threadId == "" ? (
                <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-600 after:content-[''] after:animate-dot-blink">加载中</p>
                    </div>
                </div>
            ) : isInit ? (
                <HomePage threadId={threadId as string} />
            ) : (
                <CopilotKit
                    key={threadId as string}
                    threadId={threadId as string}
                    runtimeUrl={`/api/copilotkit?userId=${userId}`}
                    agent="agent" // the name of the agent you want to use
                >
                    <AgentComponent caseId="">
                        <Chat
                            threadId={threadId as string}
                            threadStatus={thread?.status || "idle"}
                            caseId={caseId as string}
                        />
                    </AgentComponent>
                </CopilotKit>
            )}
        </div >
    );
}
