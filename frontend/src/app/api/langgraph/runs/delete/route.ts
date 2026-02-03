/**
 * LangGraph会话删除接口
 * 
 * 该接口用于删除指定的LangGraph运行，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 根据运行ID删除指定的运行
 * 2. 支持Mock数据模式
 * 3. 调用LangGraph SDK进行删除操作
 * 4. 返回删除操作结果
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
 * 删除LangGraph运行的GET接口
 * 
 * 功能说明：
 * 1. 接收GET请求，删除指定的LangGraph运行
 * 3. 根据运行ID进行删除操作
 * 4. 返回删除操作的结果
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含删除结果的响应
 *  
 * 请求参数：
 * - threadId: 查询参数，要删除的会话ID
 * - runId: 查询参数，要删除的运行ID
 * 
 * 响应格式：
 * - 成功时返回删除成功消息
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function GET(req: NextRequest) {
    console.log('[删除LangGraph运行接口] req.url', req.url);

    // 从查询参数中获取会话ID
    const threadId = req.nextUrl.searchParams.get('threadId') || '';
    const runId = req.nextUrl.searchParams.get('runId') || '';

    try {
        // 调用LangGraph SDK删除运行
        await client.runs.delete(threadId, runId);

        // 返回删除成功消息
        return NextResponse.json({ success: true, message: '删除成功' }, { status: 200 });
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}