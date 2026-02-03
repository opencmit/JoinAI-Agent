/**
 * LangGraph助手删除接口
 * 
 * 该接口用于删除指定的LangGraph助手，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 根据助手ID删除指定的助手
 * 2. 调用LangGraph SDK进行删除操作
 * 3. 返回删除操作结果
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
 * 删除LangGraph助手的POST接口
 * 
 * 功能说明：
 * 1. 接收POST请求，删除指定的LangGraph助手
 * 2. 根据助手ID进行删除操作
 * 3. 调用LangGraph SDK执行删除
 * 4. 返回删除操作的结果
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含删除结果的响应
 * 
 * 请求参数：
 * - assistantId: 要删除的助手ID
 * 
 * 响应格式：
 * - 成功时返回删除操作结果
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[删除LangGraph助手接口] req.url', req.url);

    // 获取请求体内容，提取助手ID
    const { assistantId } = await req.json();

    try {
        // 调用LangGraph SDK删除助手
        const result = await client.assistants.delete(assistantId);

        // 返回删除结果
        return NextResponse.json(result);
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}