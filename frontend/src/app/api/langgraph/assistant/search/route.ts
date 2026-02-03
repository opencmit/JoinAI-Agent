/**
 * LangGraph助手搜索接口
 * 
 * 该接口用于搜索和获取LangGraph助手列表，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 搜索现有的LangGraph助手
 * 2. 支持Mock数据模式
 * 3. 支持分页和过滤
 * 4. 返回助手列表
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";
import { SearchAssistant } from "@/types/langgraph";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 搜索LangGraph助手的GET接口
 * 
 * 功能说明：
 * 1. 接收GET请求，搜索现有的LangGraph助手
 * 3. 支持查询参数进行过滤和分页
 * 4. 返回助手列表
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含助手列表的响应
 * 
 * 请求参数：
 * - 通过URL查询参数传递SearchAssistant类型的搜索条件
 * 
 * 响应格式：
 * - 成功时返回助手列表
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[搜索LangGraph助手接口] req.url', req.url);

    try {
        // 获取请求体内容
        const payload: SearchAssistant = await req.json();

        // 调用LangGraph SDK搜索助手
        const result = await client.assistants.search(payload);

        // 返回助手列表
        return NextResponse.json({ success: true, message: '请求成功', data: result });
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}
