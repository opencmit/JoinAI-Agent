'use server'

import { Client, Thread, DefaultValues, Run } from "@langchain/langgraph-sdk";
import { CreateAssistant, UpdateAssistant, CreateThread, SearchThread, RunsCreatePayload, SearchAssistant } from "@/types/langgraph";

const LANGGRAPH_URL = process.env.LANGGRAPH_URL || "http://localhost:8000";
const LANGCHAIN_API_KEY = process.env.LANGCHAIN_API_KEY || "";
// deploymentUrl: process.env.LANGGRAPH_URL!, // make sure to replace with your real deployment url,
//             langsmithApiKey: process.env.LANGSMITH_API_KEY,
const client = new Client({
    apiKey: LANGCHAIN_API_KEY,
    apiUrl: LANGGRAPH_URL,
});

console.log("langgraph sdk client", LANGGRAPH_URL);

export async function createAssistant(payload: CreateAssistant) {
    const result = await client.assistants.create(payload);
    console.log("createAssistant", result);
    return result;
}
export async function updateAssistant(assistantId: string, payload: UpdateAssistant) {
    const result = await client.assistants.update(assistantId, payload);
    console.log("updateAssistant", result);
    return result;
}

export async function getAssistant(assistantId: string) {
    return client.assistants.get(assistantId);
}

export async function getAssistantList(query: SearchAssistant) {
    return client.assistants.search(query);
}

export async function searchAssistant(data: any) {
    const result = await client.assistants.search(data);
    return result;
}

export async function deleteAssistant(assistantId: string) {
    const result = await client.assistants.delete(assistantId);
    console.log("deleteAssistant", result);
    return result;
}

export async function createThread(payload: CreateThread) {
    const result = await client.threads.create(payload);
    console.log("createThread", result);
    return result;
}

// 删除Thread
export async function deleteThread(threadId: string) {
    return client.threads.delete(threadId);
}

// 获取Thread的列表
export async function getThreadList(payload: SearchThread): Promise<Thread<DefaultValues>[]> {
    const result = await client.threads.search(payload);
    // console.log("getThreadList", result);
    return result;
}

// 获取Thread的State
export async function getThread(threadId: string): Promise<Thread<DefaultValues>> {
    const result = await client.threads.get(threadId);

    // console.log("getThread", result);
    return result;
}

// 获取Thread的Runs
export async function getThreadRuns(threadId: string): Promise<Run[]> {
    const result = await client.runs.list(threadId);

    // console.log("getThread", result);
    return result;
}

// 更新Thread的State
export async function updateThreadState(threadId: string, values: Record<string, unknown>) {
    return client.threads.updateState(threadId, { values });
}

// 创建Run
export async function runThread(threadId: string, assistantId: string, payload?: RunsCreatePayload) {
    return client.runs.create(
        threadId,
        assistantId,
        payload
    )
}

// 更新Thread的Metadata
export async function updateThreadMetadata(threadId: string, payload: Record<string, any>) {
    const result = await client.threads.update(threadId, payload);
    // console.log("updateThreadMetadata", result);
    return result;
}

// 取消Run
export async function cancelRuns(threadId: string) {
    const runs = await client.runs.list(threadId);
    for (const run of runs) {
        await client.runs.cancel(threadId, run.run_id);
    }
    console.log("cancelRuns", runs);
    // await client.runs.cancel(threadId);
}
