/**
 * LangGraph会话创建接口
 * 
 * 该接口用于创建新的LangGraph会话，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 创建新的LangGraph会话实例
 * 2. 支持Mock数据模式
 * 3. 配置会话的基本信息
 * 4. 返回创建的会话详情
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";
import { CreateThread } from "@/types/langgraph";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 创建LangGraph会话的POST接口
 * 
 * 功能说明：
 * 1. 接收POST请求，创建新的LangGraph会话
 * 2. 支持Mock数据模式用于开发测试
 * 3. 配置会话的基本信息
 * 4. 返回创建的会话详情
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含创建的会话信息的响应
 * 
 * 请求参数：
 * - 根据CreateThread类型定义的会话配置信息
 * 
 * 响应格式：
 * - 成功时返回会话详细信息
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[创建LangGraph会话接口] req.url', req.url);

    // 获取请求体内容
    const payload: CreateThread = await req.json();

    try {
        // 调用LangGraph SDK创建会话
        const result = await client.threads.create(payload);

        // 返回创建的会话信息
        return NextResponse.json(result);
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}