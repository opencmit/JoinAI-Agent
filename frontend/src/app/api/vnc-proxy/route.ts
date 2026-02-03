import { NextRequest, NextResponse } from 'next/server';

const VNC_BASE_URL = process.env.E2B_SANDBOX_VNC || 'http://127.0.0.1:6080';

export async function GET(request: NextRequest) {
    console.log("[vnc代理接口] request.url: ", request.url);
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path') || '';

    try {
        let targetUrl = `${VNC_BASE_URL}${request.nextUrl.pathname}`;
        if (path) {
            targetUrl = `${VNC_BASE_URL}/${path}`;
        }

        targetUrl = targetUrl.replace('/api', '');
        console.log("[vnc代理接口] targetUrl: ", targetUrl);


        // 构建请求头，过滤掉不需要的头部
        const headers = new Headers();
        request.headers.forEach((value, key) => {
            if (!['host', 'origin', 'referer'].includes(key.toLowerCase())) {
                headers.set(key, value);
            }
        });

        const response = await fetch(targetUrl, {
            method: 'GET',
            headers,
        });

        // 获取响应内容
        const contentType = response.headers.get('content-type') || '';
        let data;

        if (contentType.includes('text/html') || contentType.includes('text/javascript') || contentType.includes('text/css')) {
            data = await response.text();

            // 如果是 HTML 内容，需要替换其中的绝对路径
            // if (contentType.includes('text/html')) {
            //     data = data.replace(/href="/g, 'href="/api/vnc-proxy?path=');
            //     data = data.replace(/src="/g, 'src="/api/vnc-proxy?path=');
            //     data = data.replace(/url\(['"]?\//g, 'url("/api/vnc-proxy?path=');
            // }
        } else {
            data = await response.arrayBuffer();
        }

        // 创建新的响应
        const newResponse = new NextResponse(data, {
            status: response.status,
            statusText: response.statusText,
        });

        // 复制响应头
        response.headers.forEach((value, key) => {
            if (key.toLowerCase() !== 'content-length') {
                newResponse.headers.set(key, value);
            }
        });

        return newResponse;
    } catch (error) {
        console.error('VNC proxy error:', error);
        return NextResponse.json({ error: 'VNC proxy request failed' }, { status: 500 });
    }
}

export async function POST(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path') || '';

    try {
        const targetUrl = `${VNC_BASE_URL}/${path}`;
        const body = await request.text();

        // 构建请求头，过滤掉不需要的头部
        const headers = new Headers();
        request.headers.forEach((value, key) => {
            if (!['host', 'origin', 'referer'].includes(key.toLowerCase())) {
                headers.set(key, value);
            }
        });

        const response = await fetch(targetUrl, {
            method: 'POST',
            headers,
            body,
        });

        const data = await response.text();

        const newResponse = new NextResponse(data, {
            status: response.status,
            statusText: response.statusText,
        });

        response.headers.forEach((value, key) => {
            if (key.toLowerCase() !== 'content-length') {
                newResponse.headers.set(key, value);
            }
        });

        return newResponse;
    } catch (error) {
        console.error('VNC proxy POST error:', error);
        return NextResponse.json({ error: 'VNC proxy request failed' }, { status: 500 });
    }
} 