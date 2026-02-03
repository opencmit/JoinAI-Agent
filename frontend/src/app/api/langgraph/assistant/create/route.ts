/**
 * LangGraph助手创建接口
 * 
 * 该接口用于创建新的LangGraph助手，基于LangChain LangGraph SDK，
 * 支持以下功能：
 * 1. 创建新的LangGraph助手实例
 * 2. 支持Mock数据模式
 * 3. 配置助手的基本信息
 * 4. 返回创建的助手详情
 * 
 * @author 智能体平台
 * @version 1.0.0
 */

import { NextRequest, NextResponse } from 'next/server';

import { Client } from "@langchain/langgraph-sdk";
import { CreateAssistant } from "@/types/langgraph";

// 初始化LangGraph客户端
const client = new Client({
    apiKey: process.env.LANGCHAIN_API_KEY, // LangChain API密钥
    apiUrl: process.env.LANGGRAPH_URL!, // LangGraph服务URL
});

/**
 * 创建LangGraph助手的POST接口
 * 
 * 功能说明：
 * 1. 接收POST请求，创建新的LangGraph助手
 * 2. 支持Mock数据模式用于开发测试
 * 3. 配置助手的基本信息（名称、描述等）
 * 4. 返回创建的助手详情
 * 
 * @param req - Next.js请求对象
 * @returns NextResponse - 包含创建的助手信息的响应
 * 
 * 请求参数：
 * - 根据CreateAssistant类型定义的助手配置信息
 * 
 * 响应格式：
 * - 成功时返回助手详细信息
 * - 失败时返回错误信息
 * 
 * 错误处理：
 * - 网络请求失败时返回500状态码
 * - 包含详细的错误信息
 */
export async function POST(req: NextRequest) {
    console.log('[创建LangGraph助手接口] req.url', req.url);

    // 获取请求体内容
    const payload: CreateAssistant = await req.json();

    try {
        // 调用LangGraph SDK创建助手
        const result = await client.assistants.create(payload);

        // 返回创建的助手信息
        return NextResponse.json(result);
    } catch (error: any) {
        // 错误处理：返回500状态码和错误信息
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}