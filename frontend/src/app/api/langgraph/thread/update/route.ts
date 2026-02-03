/**
 * LangGraph会话状态管理接口
 * 
 * 该接口用于获取和更新LangGraph会话状态，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 获取指定会话的当前状态
 * 2. 更新会话的状态信息
 * 3. 支持Mock数据模式
 * 4. 提供GET和POST两种操作方式
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
 * 更新LangGraph会话状态的POST接口
 * 
 * 功能说明：
 * 1. 接收POST请求，更新指定会话的状态
 * 3. 根据会话ID和更新数据修改会话状态
 * 4. 返回更新后的会话信息
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含更新后会话信息的响应
 * 
 * 请求参数：
 * - threadId: 查询参数，要更新的会话ID
 * - 请求体: 包含要更新的会话数据
 * 
 * 响应格式：
 * - 成功时返回更新后的会话信息
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[更新LangGraph会话状态接口] req.url', req.url);

    // 从查询参数中获取会话ID
    const threadId = req.nextUrl.searchParams.get('threadId') || '';

    // 获取请求体内容
    const payload = await req.json();

    try {
        // 调用LangGraph SDK更新会话状态
        const result = await client.threads.update(threadId, payload);

        // 返回更新后的会话信息
        return NextResponse.json(result);
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}