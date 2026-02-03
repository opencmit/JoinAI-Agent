"use client";

import { apiClient } from "@/lib/api-client";
// import { getDownloadUrl } from "@/lib/sandbox_manager";

export function replaceImageLinks(text: string, sandboxId: string) {
    // console.log('sandboxId', sandboxId)
    // 使用正则表达式匹配 ![alt](image.png) 或 ![](image.png) 格式
    // 匹配模式：
    // !\[ - 匹配 "![" 
    // ([^\]]*) - 匹配方括号内的alt文本（可以为空）
    // \]\( - 匹配 "]("
    // (?!https?://|ftp://|//) - 负向前瞻，排除以http://、https://、ftp://或//开头的URL
    // ([^)]+) - 匹配括号内的图片路径（非)字符）
    // \) - 匹配 ")"
    const regex = /!\[([^\]]*)\]\((?!https?:\/\/|ftp:\/\/|\/\/)([^)]+)\)/g;

    // 提取所有匹配到的文本，调用getDownloadUrl，获取下载链接，然后替换
    let replacedText = text;
    const matches = [...text.matchAll(regex)];

    for (const match of matches) {
        const [fullMatch, altText, imagePath] = match;
        // console.log('replaceImageLinks', fullMatch, altText, imagePath);

        // 跳过绝对路径的imagePath
        //   因为如果文件在沙箱，imagePath是相对路径
        //   如果是绝对路径，则认为图片不在沙箱
        if (imagePath.startsWith("/")) {
            continue;
        }

        try {
            // 获取下载链接
            // const downloadUrl = await getDownloadUrl(sandboxId, imagePath);
            // const downloadUrl = `${e2bDownloadUrl}/files?username=user&path=${imagePath}`
            // console.log("downloadUrl", downloadUrl);

            // 构建新的代理链接
            const proxyUrl = apiClient.getSandboxFileDownloadUrl(sandboxId, imagePath);

            // 如果alt文本为空，使用"image"字符串替换
            const finalAltText = altText || 'image';
            const newImageLink = `![${finalAltText}](${proxyUrl})`;

            // 替换原文本中的匹配项
            replacedText = replacedText.replace(fullMatch, newImageLink);
        } catch (error) {
            console.error(`Failed to get download URL for ${imagePath}:`, error);
        }
    }

    return replacedText;
}