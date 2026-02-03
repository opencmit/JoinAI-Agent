import { NextRequest, NextResponse } from 'next/server';

const MODEL_BASE_URL = process.env.MODEL_BASE_URL || 'http://localhost:8080';
const MODEL_API_KEY = process.env.MODEL_KEY || 'sk-123456';
const MODEL_NAME = process.env.MODEL_NAME || 'gpt-5';

export async function POST(req: NextRequest) {
    console.log('[查询模型key接口] req.url', req.url);

    const targetEndpoint = '/chat/completions';

    const { message } = await req.json();

    try {
        const apiRes = await fetch(`${MODEL_BASE_URL}${targetEndpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "Authorization": `Bearer ${MODEL_API_KEY}`
            },
            body: JSON.stringify({
                "model": MODEL_NAME,
                'messages': [
                    {
                        'role': 'user',
                        'content': `从下列话语中总结出一个标题，长度最多为10个字。**注意**：始终使用与用户问题相同的语言回答。如用户的问题为英文，则总结出的标题也需要用英文。\n\n${message}`
                    }
                ],
                "stream": false
            }),
        });
        const data = await apiRes.json();

        if (data.choices.length > 0) {
            return NextResponse.json({ success: true, title: data.choices[0].message.content });
        } else {
            return NextResponse.json({ success: false, desc: data, title: "新对话" });
        }
    } catch (error: any) {
        return NextResponse.json({ success: false, message: error?.message || '请求失败' }, { status: 500 });
    }
}