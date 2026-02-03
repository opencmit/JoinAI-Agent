"use server"
/**
 * 文件下载接口-沙箱
 */

import { NextRequest, NextResponse } from 'next/server';
import { Sandbox as CodeInterpreterSandbox } from '@e2b/code-interpreter';


/**
 * 文件下载接口-沙箱
 */
export async function GET(req: NextRequest) {
    const clientIP = req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip') || 'unknown';
    const userAgent = req.headers.get('user-agent') || 'unknown';

    try {
        console.log('[文件下载接口] 请求开始:', {
            url: req.url,
            ip: clientIP,
            userAgent
        });

        // 1. 获取路径参数
        const path = decodeURIComponent(req.nextUrl.searchParams.get('path') || '');
        const sandboxId = decodeURIComponent(req.nextUrl.searchParams.get('sandboxId') || '');

        if (!sandboxId || sandboxId.trim() === '') {
            return NextResponse.json({ error: 'sandboxId不能为空' }, { status: 400 });
        }

        // 4. 下载文件
        const sandbox = await CodeInterpreterSandbox.connect(sandboxId, {
            apiKey: process.env.E2B_API_KEY!,
        });
        if (!await sandbox.files.exists(path)) {
            return NextResponse.json({ error: '文件不存在' }, { status: 404 });
        }
        const fileContent: Blob = await sandbox.files.read(path, { format: 'blob' });

        // 7. 返回文件流（保持原始响应，但添加安全头）
        const secureResponse = new NextResponse(fileContent, {
            status: 200,
            statusText: 'OK',
            headers: {
                'Content-Type': 'application/octet-stream'
            }
        });

        return secureResponse;

    } catch (error: any) {
        console.error('[文件下载接口] 请求异常:', error);

        return NextResponse.json('服务器内部错误', { status: 500 });
    }
}