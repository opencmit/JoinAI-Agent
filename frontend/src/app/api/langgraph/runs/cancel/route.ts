/**
 * LangGraph会话取消接口
 * 
 * 该接口用于取消正在运行的LangGraph会话，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 获取会话的运行列表
 * 2. 取消正在运行或等待中的会话
 * 3. 批量取消多个运行实例
 * 4. 返回取消操作结果
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 取消LangGraph会话的POST接口
 * 
 * 功能说明：
 * 1. 接收POST请求，取消指定会话的运行实例
 * 2. 获取会话的所有运行列表
 * 3. 筛选出正在运行或等待中的实例
 * 4. 批量取消这些运行实例
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含取消操作结果的响应
 * 
 * 请求参数：
 * - threadId: 查询参数，要取消运行的会话ID
 * 
 * 响应格式：
 * - success: 操作是否成功
 * - message: 操作结果消息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[取消LangGraph会话接口] req.url', req.url);

    // 从查询参数中获取会话ID
    const threadId = req.nextUrl.searchParams.get('threadId') || '';
    const runId = req.nextUrl.searchParams.get('runId') || '';

    try {
        // 获取会话的运行列表
        const runs = await client.runs.list(threadId);

        // 遍历运行列表，取消正在运行或等待中的实例
        if (runId) {
            // 调用LangGraph SDK取消运行实例
            await client.runs.cancel(threadId, runId);
        } else {
            for (const run of runs) {
                if (run.status == "running" || run.status == "pending") {
                    // 调用LangGraph SDK取消运行实例
                    await client.runs.cancel(threadId, run.run_id);
                }
            }
        }

        // 返回取消成功消息
        return NextResponse.json({ success: true, message: '取消LangGraph会话成功' });
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}