"use server"
/**
 * 文件保存接口
 * 用于将文件保存到本地路径
 */

import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { v4 as uuidv4 } from 'uuid';

// 文件保存目录配置
const SAVE_DIRECTORY = process.env.FILE_SAVE_DIRECTORY || '/shared';

/**
 * 文件保存接口
 * 用于将文件保存到本地路径
 */
export async function POST(req: NextRequest) {
    try {
        // 获取请求体内容并解析
        const formData = await req.formData();

        // 获取文件和可选的目标路径
        const file = formData.get('file') as File;

        // 验证必要参数
        if (!file) {
            return NextResponse.json({
                success: false,
                message: '缺少文件参数'
            }, { status: 400 });
        }

        const saveName = uuidv4() + '.' + file.name.split('.').pop();

        // 确定保存路径
        const savePath = join(SAVE_DIRECTORY, saveName);

        console.log('[文件保存接口] 文件信息:', {
            name: file.name,
            size: file.size,
            type: file.type,
            saveName: saveName,
            savePath: savePath
        });


        // 确保目录存在
        const dirPath = dirname(savePath);
        try {
            await fs.mkdir(dirPath, { recursive: true });
        } catch (error: any) {
            // 如果目录已存在，忽略错误
            if (error.code !== 'EEXIST') {
                throw error;
            }
        }

        // 将文件转换为 Buffer 并保存
        const arrayBuffer = await file.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        await fs.writeFile(savePath, buffer);

        console.log('[文件保存接口] 文件保存成功:', {
            originalName: file.name,
            saveName: saveName,
            savePath: savePath,
            size: file.size
        });

        return NextResponse.json({
            success: true,
            message: '文件保存成功',
            data: {
                savePath: savePath,
                saveName: saveName,
            }
        });

    } catch (error: any) {
        console.error('[文件保存接口] 保存失败:', error);
        return NextResponse.json({
            success: false,
            message: `文件保存失败: ${error.message || '未知错误'}`
        }, { status: 500 });
    }
}