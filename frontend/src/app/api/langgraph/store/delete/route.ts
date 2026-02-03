/**
 * LangGraph删除一个item的接口
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
 * LangGraph删除一个item的接口
 */
export async function POST(req: NextRequest) {
    console.log('[LangGraph删除一个item的接口] req.url', req.url);

    // 获取请求体内容
    const payload: { namespace: string[], key: string } = await req.json();

    try {
        // 调用LangGraph SDK删除一个item
        const result = await client.store.deleteItem(payload.namespace, payload.key);

        // 返回删除成功消息
        return NextResponse.json({ success: true, message: '请求成功', data: result });
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}