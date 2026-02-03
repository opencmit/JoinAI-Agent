/**
 * LangGraph会话运行列表接口
 * 
 * 该接口用于获取LangGraph会话的运行列表，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 获取会话的运行列表
 * 2. 支持Mock数据模式用于开发测试
 * 3. 支持搜索条件过滤运行列表
 * 4. 返回运行列表数据
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";
import { ListRuns } from "@/types/langgraph";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 获取LangGraph会话运行列表的POST接口 
 * 
 * 功能说明：
 * 1. 接收POST请求，获取指定会话的运行列表
 * 3. 支持搜索条件过滤运行列表
 * 4. 返回运行列表数据
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含运行列表数据的响应
 * 
 * 请求参数：
 * - threadId: 查询参数，要获取运行列表的会话ID
 * - 根据ListRuns类型定义的搜索条件
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
    console.log('[获取LangGraph会话运行列表接口] req.url', req.url);

    // 从查询参数中获取会话ID
    const threadId = req.nextUrl.searchParams.get('threadId') || '';

    // 获取请求体内容
    const payload: ListRuns = await req.json();

    try {
        // 获取会话的运行列表
        const result = await client.runs.list(threadId, payload);

        // 返回会话列表数据
        return NextResponse.json({ success: true, message: '请求成功', data: result });
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}