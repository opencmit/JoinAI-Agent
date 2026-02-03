/**
 * LangGraph助手更新接口
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";
import { UpdateAssistant } from "@/types/langgraph";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 更新LangGraph助手的POST接口
 */
export async function POST(req: NextRequest) {
    console.log('[更新LangGraph助手接口] req.url', req.url);

    // 从查询参数中获取assistant_id
    const assistantId = req.nextUrl.searchParams.get('assistantId') || '';

    // 获取请求体内容
    const payload: UpdateAssistant = await req.json();

    try {
        // 调用LangGraph SDK创建助手
        const result = await client.assistants.update(assistantId, payload);

        // 返回更新的助手信息
        return NextResponse.json(result);
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}