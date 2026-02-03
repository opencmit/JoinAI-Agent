"use client";

import "tdesign-react/es/_util/react-19-adapter";
import React, { useState, useEffect } from 'react';
import { FileText, AlertTriangle, CircleDashed, Folder, FolderOpen, File, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Tooltip, List, Button as TButton } from 'tdesign-react';
import { ChevronRightIcon, ChevronLeftIcon } from 'tdesign-icons-react';

import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";

import ExcelJS from "exceljs";
import { apiClient } from "@/lib/api-client";

// 动画变体定义
const slideVariants = {
    enterLeft: {
        x: '100%',
        opacity: 0
    },
    enterRight: {
        x: '-100%',
        opacity: 0
    },
    center: {
        x: 0,
        opacity: 1
    },
    exitLeft: {
        x: '-100%',
        opacity: 0
    },
    exitRight: {
        x: '100%',
        opacity: 0
    }
};

// Office 文档预览组件将使用动态导入来加载所需的库

// Iframe 内容组件，用于样式隔离
const IframeContent = ({
    url,
    className = ''
}: {
    url: string;
    maxHeight?: string;
    fontSize?: string;
    lineHeight?: string;
    className?: string;
}) => {
    const [iframeKey, setIframeKey] = useState(0);

    // 当内容变化时重新生成 iframe
    useEffect(() => {
        setIframeKey(prev => prev + 1);
    }, [url]);

    return (
        <iframe
            key={iframeKey}
            src={url}
            className={cn("w-full border-0 h-full", className)}
            style={{
                overflow: 'auto',
                borderRadius: '4px'
            }}
            title="Content Preview"
            onLoad={() => {
                // 清理 URL 对象
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            }}
        />
    );
};

const FILE_ICON_MAP = {
    "doc": "/file-doc.svg",
    "docx": "/file-doc.svg",
    "xls": "/file-xls.svg",
    "xlsx": "/file-xls.svg",
    "ppt": "/file-ppt.svg",
    "pptx": "/file-ppt.svg",
    "pdf": "/file-pdf.svg",
    "txt": "/file-txt.svg",
}

export interface FileOperation {
    operation: string;
    path?: string;
    content?: string;
    old_str?: string;
    new_str?: string;
    files?: Array<{ file_path: string, content: string }>;
    result?: string;
    fileName?: string;
    filePath?: string;
    fileDate?: string;
    isLoading?: boolean;
    isSuccess?: boolean;
}

interface FilesTaskProps {
    operation?: FileOperation | FileOperation[];
    workingDirectory?: string;
    sandboxId?: string;
}

const formatHtml = (body: string) => {
    return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>
                ${body}
            </body>
            </html>
        `;
}

export const FilesTask = React.memo(function FilesTask({
    operation,
    workingDirectory = "/workspace",
    sandboxId
}: FilesTaskProps) {
    const [selectedOperation, setSelectedOperation] = useState<FileOperation | null>(null);
    const { ListItem, ListItemMeta } = List;

    // 支持的文本文件扩展名
    const supportedTextExtensions = ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c', '.h', '.log', '.csv', '.yaml', '.yml', '.jsx', '.tsx', '.vue', '.php', '.rb', '.go', '.rs', '.sh', '.bat', '.sql', '.ini', '.conf', '.cfg'];

    // 检查文件是否为支持的文本文件
    const isTextFile = (filePath: string) => {
        if (!filePath) return false;
        return supportedTextExtensions.some(ext => filePath.toLowerCase().endsWith(ext));
    };

    // 检查文件是否为HTML文件
    const isHtmlFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.html') || filePath.toLowerCase().endsWith('.htm');
    };

    // 检查文件是否为PDF文件
    const isPdfFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.pdf');
    };

    // 检查文件是否为PPT文件
    const isPptFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.ppt') || filePath.toLowerCase().endsWith('.pptx');
    };

    // 检查文件是否为DOC文件
    const isDocFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.doc') || filePath.toLowerCase().endsWith('.docx');
    };

    // 检查文件是否为Excel文件
    const isExcelFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.xls') || filePath.toLowerCase().endsWith('.xlsx');
    };

    // 检查文件是否为Markdown文件
    const isMarkdownFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.md') || filePath.toLowerCase().endsWith('.markdown');
    };

    // 检查文件是否为Python文件
    const isPythonFile = (filePath: string) => {
        if (!filePath) return false;
        return filePath.toLowerCase().endsWith('.py');
    };

    // Office 文档预览组件
    const OfficeFilePreview = ({ filePath }: { filePath: string }) => {
        const [previewContent, setPreviewContent] = useState<string>('');
        const [isLoading, setIsLoading] = useState(true);
        const [error, setError] = useState<string>('');

        useEffect(() => {
            const generatePreview = async () => {
                try {
                    setIsLoading(true);
                    setError('');

                    // 确保在客户端环境下才处理 Office 文档
                    if (typeof window === 'undefined') {
                        setError('服务器端不支持 Office 文档预览');
                        return;
                    }

                    // 通过 filePath URL 获取文件内容
                    let fileContent: ArrayBuffer;
                    try {
                        // 使用安全下载接口获取文件内容
                        const blob = await apiClient.secureDownloadSandboxFile(sandboxId || "", filePath);
                        fileContent = await blob.arrayBuffer();
                    } catch (fetchErr) {
                        console.error('获取文件失败:', fetchErr);
                        setError('无法获取文件内容，请检查文件路径');
                        return;
                    }

                    if (isDocFile(filePath)) {
                        // Word 文档预览
                        try {
                            const mammothModule = await import('mammoth');
                            const result = await mammothModule.default.convertToHtml({ arrayBuffer: fileContent });
                            const htmlDocument = formatHtml(result.value);
                            const blob = new Blob([htmlDocument], { type: 'text/html' });
                            const url = URL.createObjectURL(blob);
                            setPreviewContent(url);
                        } catch (err) {
                            console.error('Word 文档处理失败:', err);
                            setError('Word 文档格式不支持或文件损坏');
                        }
                    } else if (isExcelFile(filePath)) {
                        // Excel 文件预览
                        try {
                            const workbook = new ExcelJS.Workbook();
                            await workbook.xlsx.load(fileContent);

                            // 获取第一个工作表
                            const worksheet = workbook.worksheets[0];
                            if (!worksheet) {
                                throw new Error('工作簿中没有工作表');
                            }

                            // 将工作表转换为HTML
                            let html = '<table border="1" style="border-collapse: collapse; width: 100%;">';

                            // 遍历所有行和列
                            worksheet.eachRow((row: ExcelJS.Row, rowNumber: number) => {
                                html += '<tr>';
                                row.eachCell((cell: ExcelJS.Cell, colNumber: number) => {
                                    console.log(rowNumber, colNumber);
                                    const cellValue = cell.value || '';
                                    const cellType = typeof cellValue;
                                    let displayValue = '';

                                    if (cellType === 'object' && cellValue !== null) {
                                        if ((cellValue as any).richText) {
                                            displayValue = (cellValue as any).richText.map((rt: any) => rt.text).join('');
                                        } else if ((cellValue as any).formula) {
                                            displayValue = (cellValue as any).formula;
                                        } else if ((cellValue as any).result) {
                                            displayValue = (cellValue as any).result;
                                        } else {
                                            displayValue = String(cellValue);
                                        }
                                    } else {
                                        displayValue = String(cellValue);
                                    }

                                    html += `<td style="padding: 4px; border: 1px solid #ccc;">${displayValue}</td>`;
                                });
                                html += '</tr>';
                            });

                            html += '</table>';

                            const htmlDocument = formatHtml(html);
                            const blob = new Blob([htmlDocument], { type: 'text/html' });
                            const url = URL.createObjectURL(blob);
                            setPreviewContent(url);
                        } catch (err) {
                            console.error('Excel 文件处理失败:', err);
                            setError('Excel 文件格式不支持或文件损坏');
                        }
                    } else if (isPptFile(filePath)) {
                        // PowerPoint 文件预览 - 显示基本信息
                        setPreviewContent(`
                            <div style="padding: 20px; text-align: center;">
                                <h3>PowerPoint 文件预览</h3>
                                <p>文件大小: ${(fileContent.byteLength / 1024).toFixed(2)} KB</p>
                                <p>请下载文件后在本地查看完整内容</p>
                            </div>
                        `);
                    }
                } catch (err) {
                    console.error('生成预览失败:', err);
                    setError('预览生成失败，请下载文件查看');
                } finally {
                    setIsLoading(false);
                }
            };

            generatePreview();
        }, [filePath]);

        if (isLoading) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center w-full max-w-xs">
                        <CircleDashed className="h-6 w-6 text-blue-400 animate-spin mx-auto mb-2" />
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 after:content-[''] after:animate-dot-blink">正在加载文档</div>
                    </div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center">
                        <AlertTriangle className="h-6 w-6 text-amber-400 mx-auto mb-2" />
                        <div className="text-sm text-amber-600 dark:text-amber-400">{error}</div>
                        <div className="text-xs text-amber-500 dark:text-amber-500 mt-1">
                            请使用上方下载按钮下载文件查看
                        </div>
                    </div>
                </div>
            );
        }

        return (
            <IframeContent
                url={previewContent}
                fontSize='14px'
                lineHeight='1.5'
                className="bg-white dark:bg-zinc-900"
            />
        );
    };

    // Python 文件预览组件
    const PythonFilePreview = ({ filePath }: { filePath: string }) => {
        const [content, setContent] = useState<string>('');
        const [isLoading, setIsLoading] = useState(true);
        const [error, setError] = useState<string>('');

        useEffect(() => {
            const loadPythonContent = async () => {
                try {
                    setIsLoading(true);
                    setError('');

                    // 使用安全下载接口获取文件内容
                    const blob = await apiClient.secureDownloadSandboxFile(sandboxId || "", filePath);
                    const content = await blob.text();
                    setContent(content);
                } catch (fetchErr) {
                    console.error('获取Python文件失败:', fetchErr);

                    if (fetchErr instanceof Error) {
                        if (fetchErr.name === 'AbortError') {
                            setError('请求超时，请检查网络连接或稍后重试');
                        } else if (fetchErr.message.includes('HTTP error! status: 404')) {
                            setError('文件未找到，请检查文件路径是否正确');
                        } else if (fetchErr.message.includes('HTTP error! status: 403')) {
                            setError('没有权限访问此文件，请检查认证信息');
                        } else if (fetchErr.message.includes('HTTP error! status: 500')) {
                            setError('服务器内部错误，请稍后重试');
                        } else {
                            setError(`获取文件失败: ${fetchErr.message}`);
                        }
                    } else {
                        setError('无法获取文件内容，请检查文件路径和网络连接');
                    }
                } finally {
                    setTimeout(() => {
                        setIsLoading(false);
                    }, 1000);
                }
            };

            loadPythonContent();
        }, [filePath]);

        if (isLoading) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center w-full max-w-xs">
                        <CircleDashed className="h-6 w-6 text-blue-400 animate-spin mx-auto mb-2" />
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 after:content-[''] after:animate-dot-blink">正在加载Python文件</div>
                    </div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center">
                        <AlertTriangle className="h-6 w-6 text-amber-400 mx-auto mb-2" />
                        <div className="text-sm text-amber-600 dark:text-amber-400">{error}</div>
                        <div className="text-xs text-amber-500 dark:text-amber-500 mt-1">
                            请使用上方下载按钮下载文件查看
                        </div>
                    </div>
                </div>
            );
        }

        // 将内容按行分割
        const lines = content.split('\\n');

        return (
            <div className="bg-gray-50 dark:bg-gray-900 h-full overflow-y-auto custom-scrollbar">
                <div className="font-mono text-sm">
                    {lines.map((line, index) => (
                        <div key={index} className="flex hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                            {/* 行号 */}
                            <div className="flex-shrink-0 w-12 px-3 py-1 text-right text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 select-none">
                                {index + 1}
                            </div>
                            {/* 代码内容 */}
                            <div className="flex-1 px-3 py-1 text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words">
                                {line || '\u00A0'} {/* 空行显示为空格 */}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    // Markdown 文件预览组件
    const MarkdownFilePreview = ({ filePath, type }: { filePath: string, type: string }) => {
        const [markdownContent, setMarkdownContent] = useState<string>('');
        const [isLoading, setIsLoading] = useState(true);
        const [error, setError] = useState<string>('');

        useEffect(() => {
            const loadMarkdownContent = async () => {
                try {
                    setIsLoading(true);
                    setError('');

                    // 使用安全下载接口获取文件内容
                    const blob = await apiClient.secureDownloadSandboxFile(sandboxId || "", filePath);
                    let content = await blob.text();
                    if (type === 'python') {
                        content = `\`\`\`python\n${content}\n\`\`\``;
                    }

                    setMarkdownContent(content);
                } catch (fetchErr) {
                    console.error('获取Markdown文件失败:', fetchErr);

                    // 根据错误类型提供更具体的错误信息
                    if (fetchErr instanceof Error) {
                        if (fetchErr.name === 'AbortError') {
                            setError('请求超时，请检查网络连接或稍后重试');
                        } else if (fetchErr.message.includes('HTTP error! status: 404')) {
                            setError('文件未找到，请检查文件路径是否正确');
                        } else if (fetchErr.message.includes('HTTP error! status: 403')) {
                            setError('没有权限访问此文件，请检查认证信息');
                        } else if (fetchErr.message.includes('HTTP error! status: 500')) {
                            setError('服务器内部错误，请稍后重试');
                        } else {
                            setError(`获取文件失败: ${fetchErr.message}`);
                        }
                    } else {
                        setError('无法获取文件内容，请检查文件路径和网络连接');
                    }
                } finally {
                    setTimeout(() => {
                        setIsLoading(false);
                    }, 2000)
                }
            };

            loadMarkdownContent();
        }, [filePath]);

        if (isLoading) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center w-full max-w-xs">
                        <CircleDashed className="h-6 w-6 text-blue-400 animate-spin mx-auto mb-2" />
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 after:content-[''] after:animate-dot-blink">正在加载Markdown</div>
                    </div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center">
                        <AlertTriangle className="h-6 w-6 text-amber-400 mx-auto mb-2" />
                        <div className="text-sm text-amber-600 dark:text-amber-400">{error}</div>
                        <div className="text-xs text-amber-500 dark:text-amber-500 mt-1">
                            请使用上方下载按钮下载文件查看
                        </div>
                    </div>
                </div>
            );
        }

        return (
            <div className="bg-transparent h-full pl-4 pr-2 py-4 overflow-y-auto custom-scrollbar">
                <MarkdownText>{markdownContent}</MarkdownText>
            </div>
        );
    };

    // 其他文件预览组件
    const OtherFilePreview = ({ filePath }: { filePath: string }) => {
        const [content, setContent] = useState<string>('');
        const [isLoading, setIsLoading] = useState(true);
        const [error, setError] = useState<string>('');

        useEffect(() => {
            const loadContent = async () => {
                try {
                    setIsLoading(true);
                    setError('');

                    // 使用安全下载接口获取文件内容
                    const blob = await apiClient.secureDownloadSandboxFile(sandboxId || "", filePath);
                    const content = await blob.text();

                    setContent(content);
                } catch (fetchErr) {
                    console.error('获取其他文件失败:', fetchErr);

                    // 根据错误类型提供更具体的错误信息
                    if (fetchErr instanceof Error) {
                        if (fetchErr.name === 'AbortError') {
                            setError('请求超时，请检查网络连接或稍后重试');
                        } else if (fetchErr.message.includes('HTTP error! status: 404')) {
                            setError('文件未找到，请检查文件路径是否正确');
                        } else if (fetchErr.message.includes('HTTP error! status: 403')) {
                            setError('没有权限访问此文件，请检查认证信息');
                        } else if (fetchErr.message.includes('HTTP error! status: 500')) {
                            setError('服务器内部错误，请稍后重试');
                        } else {
                            setError(`获取文件失败: ${fetchErr.message}`);
                        }
                    } else {
                        setError('无法获取文件内容，请检查文件路径和网络连接');
                    }
                } finally {
                    setTimeout(() => {
                        setIsLoading(false);
                    }, 2000)
                }
            };

            loadContent();
        }, [filePath]);

        if (isLoading) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center w-full max-w-xs">
                        <CircleDashed className="h-6 w-6 text-blue-400 animate-spin mx-auto mb-2" />
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 after:content-[''] after:animate-dot-blink">正在加载文件</div>
                    </div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex items-center justify-center h-32 bg-transparent rounded">
                    <div className="text-center">
                        <AlertTriangle className="h-6 w-6 text-amber-400 mx-auto mb-2" />
                        <div className="text-sm text-amber-600 dark:text-amber-400">{error}</div>
                        <div className="text-xs text-amber-500 dark:text-amber-500 mt-1">
                            请使用上方下载按钮下载文件查看
                        </div>
                    </div>
                </div>
            );
        }

        return (
            <div className="bg-transparent h-full pl-4 pr-2 py-4 overflow-y-auto custom-scrollbar">
                <MarkdownText>{content}</MarkdownText>
            </div>
        );
    };

    // 下载文件功能 - 使用安全下载接口
    const downloadFile = async (filePath: string) => {
        if (!filePath) {
            console.error('缺少 文件路径');
            return;
        }

        try {
            // 使用安全下载接口获取文件Blob
            const blob = await apiClient.secureDownloadSandboxFile(sandboxId || "", filePath);

            // 创建Blob URL并触发下载
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = getFileName(filePath);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // 清理Blob URL
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('下载文件失败:', error);
        }
    };

    // 下载文件内容功能 - 用于没有 sandboxId 的情况
    const downloadFileContent = (content: string, filename: string) => {
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || 'file.txt';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    // 获取文件名
    const getFileName = (path?: string) => {
        if (!path) return 'file.txt';
        return path.split('/').pop() || 'file.txt';
    };

    // 判断是否为写操作（包含文件内容在args中）
    const isWriteOperation = (op: string) => {
        return ['create', 'write', 'str_replace', 'batch_write'].includes(op);
    };

    // 判断是否为读操作（文件内容在result中）
    const isReadOperation = (op: string) => {
        return op === 'read';
    };

    // 判断是否为目录操作
    // const isDirectoryOperation = (op: string) => {
    //     return ['list', 'mkdir', 'watch'].includes(op);
    // };

    // 判断是否为文件操作
    // const isFileOperation = (op: string) => {
    //     return ['create', 'read', 'write', 'delete', 'str_replace'].includes(op);
    // };

    // 从读操作结果中提取文件内容
    const extractFileContentFromResult = (result: string) => {
        if (result.startsWith('文件内容:\n')) {
            return result.substring('文件内容:\n'.length);
        }
        return result;
    };

    // 获取要显示的文件内容
    const getDisplayContent = (operation: FileOperation) => {
        if (isWriteOperation(operation.operation)) {
            // 写操作：内容在 operation.content 中
            return operation.content;
        } else if (isReadOperation(operation.operation) && operation.result) {
            // 读操作：内容在 operation.result 中，需要提取
            return extractFileContentFromResult(operation.result);
        }
        return null;
    };

    // 检查是否可以显示文件内容
    const canDisplayContent = (operation: FileOperation) => {
        if (!operation.path) return true; // 如果没有路径，默认可以显示

        let result = false;
        result = result || isTextFile(operation.fileName || operation.path);
        result = result || isHtmlFile(operation.fileName || operation.path);
        result = result || isPdfFile(operation.fileName || operation.path);
        result = result || isPptFile(operation.fileName || operation.path);
        result = result || isDocFile(operation.fileName || operation.path);
        result = result || isExcelFile(operation.fileName || operation.path);
        return result;
    };

    const getOperationIcon = (op: string) => {
        switch (op) {
            case 'create':
            case 'write':
            case 'batch_write':
                return <File className="h-4 w-4" />;
            case 'read':
                return <FileText className="h-4 w-4" />;
            case 'delete':
                return <File className="h-4 w-4" />;
            case 'list':
            case 'watch':
                return <FolderOpen className="h-4 w-4" />;
            case 'mkdir':
                return <Folder className="h-4 w-4" />;
            case 'str_replace':
                return <FileText className="h-4 w-4" />;
            default:
                return <FileText className="h-4 w-4" />;
        }
    };

    const getOperationTitle = (op: string) => {
        switch (op) {
            case 'create': return '创建文件';
            case 'read': return '读取文件';
            case 'write': return '重写文件';
            case 'delete': return '删除文件';
            case 'list': return '列出目录';
            case 'mkdir': return '创建目录';
            case 'str_replace': return '替换文本';
            case 'watch': return '监视目录';
            case 'batch_write': return '批量写入';
            default: return '文件操作';
        }
    };

    const getOperationDescription = (op: FileOperation) => {
        switch (op.operation) {
            case 'create':
                return `${op.path}`;
            case 'read':
                return `${op.path}`;
            case 'write':
                return `${op.path}`;
            case 'delete':
                return `${op.path}`;
            case 'list':
                return `${op.path || workingDirectory}`;
            case 'mkdir':
                return `${op.path}`;
            case 'str_replace':
                return `${op.path}`;
            case 'watch':
                return `${op.path || workingDirectory}`;
            case 'batch_write':
                return `${op.files?.map(f => f.file_path).join(', ') || ''}`;
            default:
                return op.fileName;
        }
    };

    // 格式化文件内容展示
    const formatContent = (content: string) => {
        return content;
    };

    // 渲染文件内容区域
    const RenderFileContent = React.memo(function RenderFileContent({ operation, sandboxId }: { operation: FileOperation, sandboxId: string }) {
        // 检查是否可以显示内容
        if (canDisplayContent(operation)) {
            return <RenderSingleFileContent fileName={operation.fileName || ""} filePath={operation.filePath || ""} isBatchFile={false} sandboxId={sandboxId || ""} />;
        } else {
            const displayContent = getDisplayContent(operation);

            if (displayContent) {
                return (
                    <pre className="text-xs whitespace-pre-wrap break-words text-zinc-800 dark:text-zinc-200 p-3 rounded min-h-0 flex-1">
                        {formatContent(displayContent)}
                    </pre>
                );
            } else {

                return (
                    <div className="bg-amber-50 dark:bg-amber-900/20 p-3 rounded border border-amber-200 dark:border-amber-800/30 flex items-center gap-2 text-amber-700 dark:text-amber-300">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="text-sm">
                            不支持预览此文件类型，但可以使用上方下载按钮下载文件。支持预览的文件类型: {supportedTextExtensions.join(', ')}
                        </span>
                    </div>
                );
            }
        }
    }, (prevProps, nextProps) => {
        // 自定义比较函数，只在真正变化时重新渲染
        return prevProps.operation.path === nextProps.operation.path
    });

    // 渲染str_replace操作的特殊内容
    const RenderStrReplaceContent = React.memo(function RenderStrReplaceContent({ operation }: { operation: FileOperation }) {
        if (operation.operation !== 'str_replace') return null;

        return (
            <div className="space-y-2">
                {operation.old_str && (
                    <div className="bg-rose-50 dark:bg-rose-900/20 p-3 rounded border border-rose-200 dark:border-rose-800/30">
                        <pre className="text-xs whitespace-pre-wrap break-words text-zinc-800 dark:text-zinc-200">
                            {operation.old_str}
                        </pre>
                    </div>
                )}
                {operation.new_str && (
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 p-3 rounded border border-emerald-200 dark:border-emerald-800/30">
                        <pre className="text-xs whitespace-pre-wrap break-words text-zinc-800 dark:text-zinc-200">
                            {operation.new_str}
                        </pre>
                    </div>
                )}
            </div>
        );
    }, (prevProps, nextProps) => {
        // 自定义比较函数，只在真正变化时重新渲染
        return prevProps.operation === nextProps.operation
    });

    // 渲染单个文件内容的辅助函数
    const RenderSingleFileContent = React.memo(function RenderSingleFileContent({ fileName, filePath, isBatchFile, sandboxId }: { fileName: string, filePath: string, isBatchFile: boolean, sandboxId: string }) {
        // 如果是HTML文件
        if (isHtmlFile(fileName)) {
            return (
                <IframeContent
                    url={apiClient.getSandboxFileDownloadUrl(sandboxId || "", filePath)}
                    fontSize={isBatchFile ? '12px' : '14px'}
                    lineHeight={isBatchFile ? '1.4' : '1.5'}
                    className="bg-white dark:bg-zinc-900"
                />
            );
        }

        // 如果是Markdown文件
        if (isMarkdownFile(fileName)) {
            return (
                <div className="h-full overflow-hidden">
                    <MarkdownFilePreview filePath={filePath} type="normal" />
                </div>
            );
        }

        // 如果是PDF文件
        if (isPdfFile(fileName)) {
            return (
                <div className="h-full border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                    <IframeContent
                        url={apiClient.getSandboxFileDownloadUrl(sandboxId || "", filePath)}
                        fontSize={isBatchFile ? '12px' : '14px'}
                        lineHeight={isBatchFile ? '1.4' : '1.5'}
                        className="bg-white dark:bg-zinc-900"
                    />
                </div>
            );
        }

        // 如果是PPT文件
        if (isPptFile(fileName)) {
            return (
                <div className="border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                    <div className="bg-white dark:bg-zinc-900 p-4">
                        <div className="flex items-center justify-center h-32 bg-gray-50 dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600">
                            <div className="text-center">
                                <div className="text-3xl mb-2">📊</div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                    PowerPoint 文件预览
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                    请下载文件后在本地查看
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        // 如果是DOC文件
        if (isDocFile(fileName)) {
            return (
                <div className="h-full border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                    <OfficeFilePreview filePath={filePath} />
                </div>
            );
        }

        // 如果是Excel文件
        if (isExcelFile(fileName)) {
            return (
                <div className="h-full border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                    <OfficeFilePreview filePath={filePath} />
                </div>
            );
        }

        // 如果是Python文件
        if (isPythonFile(fileName)) {
            return (
                <div className="h-full border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                    <PythonFilePreview filePath={filePath} />
                </div>
            );
        }

        // 默认文本文件显示
        return (
            <div className="h-full border border-zinc-200 dark:border-zinc-700 rounded overflow-hidden">
                <OtherFilePreview filePath={filePath} />
            </div>
        );
    }, (prevProps, nextProps) => {
        // 自定义比较函数，只在真正变化时重新渲染
        return prevProps.filePath === nextProps.filePath
    });

    // 渲染批量写入文件列表
    const renderBatchWriteFiles = (operation: FileOperation) => {
        if (operation.operation !== 'batch_write' || !operation.files) return null;

        return (
            <div className="space-y-2">
                {operation.files.map((file, index) => (
                    <div key={index} className="p-3 rounded border border-zinc-200 dark:border-zinc-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium max-w-20 text-zinc-600 dark:text-zinc-400">
                                {file.file_path}
                            </span>
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                    if (sandboxId) {
                                        downloadFile(file.file_path);
                                    } else {
                                        downloadFileContent(file.content, getFileName(file.file_path));
                                    }
                                }}
                                className="h-6 px-2"
                                title={sandboxId ? "下载文件" : "下载文件内容"}
                            >
                                <Download className="h-3 w-3" />
                            </Button>
                        </div>
                        <RenderSingleFileContent fileName={file.file_path} filePath={file.file_path} isBatchFile={true} sandboxId={sandboxId || ""} />;
                    </div>
                ))}
            </div>
        );
    };

    // 渲染操作结果内容
    // const renderResultContent = (operation: FileOperation) => {
    //     if (!operation.result || isReadOperation(operation.operation)) return null;

    //     return (
    //         <div className="p-3 rounded border border-zinc-200 dark:border-zinc-700">
    //             <pre className="text-xs whitespace-pre-wrap break-words text-zinc-800 dark:text-zinc-200">
    //                 {operation.result}
    //             </pre>
    //         </div>
    //     );
    // };

    return (
        <>
            {operation instanceof Array ? (
                // 用户点击【文件tab】，进入全部文件展示状态
                operation.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 text-zinc-400 dark:text-zinc-600">
                        <span>暂无文件操作</span>
                    </div>
                ) : (
                    <div className="relative h-full overflow-hidden">
                        <AnimatePresence mode="wait">
                            {selectedOperation ? (
                                // 单个文件预览展示
                                <motion.div
                                    key="detail"
                                    className='flex flex-col h-full bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] rounded-t-lg'
                                    initial='enterLeft'
                                    animate="center"
                                    exit='exitRight'
                                    variants={slideVariants}
                                    transition={{ duration: 0.3, ease: 'easeOut' }}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1 flex flex-row items-center">
                                            <TButton size="large" shape="circle" variant="text" onClick={() => {
                                                setSelectedOperation(null);
                                            }}>
                                                <ChevronLeftIcon className="h-4 w-4" />
                                            </TButton>
                                            <span className="flex-1 text-sm font-medium text-zinc-800 w-60 truncate pr-2">
                                                {selectedOperation.fileName}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex-1 bg-transparent overflow-y-auto">
                                        <div className="h-full text-zinc-800 bg-transparent space-y-3">
                                            {selectedOperation && (
                                                <>
                                                    {/* str_replace 操作的特殊显示 */}
                                                    <RenderStrReplaceContent operation={selectedOperation} />

                                                    {/* 批量写入文件列表 */}
                                                    {renderBatchWriteFiles(selectedOperation)}

                                                    {/* 文件内容显示 */}
                                                    <RenderFileContent operation={selectedOperation} sandboxId={sandboxId || ""} />

                                                    {/* 操作结果显示 */}
                                                    {/* {renderResultContent(operation)} */}

                                                    {selectedOperation.isLoading && (
                                                        <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
                                                            <CircleDashed className="h-3 w-3 text-blue-400 animate-spin" />
                                                            <span className="tracking-wide">文件操作执行中...</span>
                                                        </div>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                // 文件列表展示
                                <motion.div
                                    key="list"
                                    initial='enterRight'
                                    animate="center"
                                    exit='exitLeft'
                                    variants={slideVariants}
                                    transition={{ duration: 0.3, ease: 'easeOut' }}
                                >
                                    <List
                                        className="h-full bg-linear-122 from-[#EFF3FC] via-[#FDFEFF6B] to-[#F9FAFE19] px-4 py-2"
                                        style={{
                                            background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                                            borderRadius: '10px',
                                            color: '#363B64',
                                            fontFamily: 'PingFang SC',
                                            fontWeight: 'regular',
                                            fontSize: '14px',
                                            lineHeight: '14px',
                                            letterSpacing: '0px',
                                            textAlign: 'left',
                                            overflow: 'hidden',
                                        }}
                                    >
                                        {operation.map((op, index) => (
                                            <ListItem
                                                key={index}
                                                action={
                                                    <div className='flex items-center gap-2'>
                                                        {/* 状态指示器 */}
                                                        {op && !op.isLoading && (
                                                            <span
                                                                className={cn(
                                                                    'text-xs flex items-center',
                                                                    op.isSuccess
                                                                        ? 'text-emerald-500 dark:text-emerald-400'
                                                                        : 'text-rose-500 dark:text-rose-400',
                                                                )}
                                                            >
                                                                <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                                                {op.isSuccess ? '成功' : '失败'}
                                                            </span>
                                                        )}
                                                        {/* 下载按钮 - 支持所有文件类型 */}
                                                        {op && op.path && sandboxId && (
                                                            <Button
                                                                size="sm"
                                                                variant="ghost"
                                                                onClick={() => downloadFile(op.path!)}
                                                                className="h-6 px-2"
                                                                title="下载文件"
                                                            >
                                                                <Download className="h-3 w-3" />
                                                                下载
                                                            </Button>
                                                        )}
                                                        {/* 下载按钮 - 当没有 sandboxId 但有文件内容时，使用内容下载 */}
                                                        {op && !sandboxId && getDisplayContent(op) && canDisplayContent(op) && (
                                                            <Button
                                                                size="sm"
                                                                variant="ghost"
                                                                onClick={() => {
                                                                    const content = getDisplayContent(op);
                                                                    if (content) {
                                                                        downloadFileContent(content, getFileName(op.path));
                                                                    }
                                                                }}
                                                                className="h-6 px-2"
                                                                title="下载文件内容"
                                                            >
                                                                <Download className="h-3 w-3" />
                                                            </Button>
                                                        )}
                                                        <TButton size="large" shape="circle" variant="text" onClick={() => {
                                                            setSelectedOperation(op);
                                                        }}>
                                                            <ChevronRightIcon className="h-5 w-5" />
                                                        </TButton>
                                                    </div>
                                                }
                                                style={{
                                                    background: 'linear-gradient(122.45deg, #EFF3FC 0%, #FDFEFF6B 44%, #F9FAFE19 100%)',
                                                }}
                                            >
                                                <ListItemMeta title={
                                                    <Tooltip content={op.path} placement="top" showArrow destroyOnClose>
                                                        <div className='flex items-center'>
                                                            <img
                                                                src={FILE_ICON_MAP[op.path?.split('.').pop() as keyof typeof FILE_ICON_MAP] || "/file-attachment.svg"}
                                                                alt="Python file"
                                                                className="w-4 h-4 mr-2 inline-block"
                                                            />
                                                            <span className="max-w-60 truncate">{op.fileName || op.path}</span>
                                                        </div>
                                                    </Tooltip>
                                                } description={op.fileDate} />
                                            </ListItem>
                                        ))}
                                    </List>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )
            ) : (
                // 用户点击【聚智桌面】，单个文件的预览展示
                <div className="border border-zinc-200/100 dark:border-zinc-800/50 rounded-xl overflow-hidden flex flex-col h-full bg-gradient-to-b from-zinc-50/50 to-zinc-100/30 dark:from-zinc-950/50 dark:to-zinc-900/30">
                    <div className="flex items-center p-3 bg-gradient-to-r from-zinc-100/80 to-zinc-200/50 dark:from-zinc-900/80 dark:to-zinc-800/50 justify-between border-b border-zinc-200/30 dark:border-zinc-800/30">

                        <Tooltip content={operation ? `${getOperationTitle(operation.operation)} - ${getOperationDescription(operation)}` : '文件操作'} placement="top" showArrow destroyOnClose>
                            <div className="flex items-center">
                                {operation && getOperationIcon(operation.operation)}
                                <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 tracking-wide ml-2 max-w-90 2xl:max-w-100 truncate">
                                    {operation ? `${getOperationTitle(operation.operation)} - ${getOperationDescription(operation)}` : '文件操作'}
                                </span>
                            </div>
                        </Tooltip>
                        <div className="flex items-center gap-2">
                            {/* 下载按钮 - 支持所有文件类型 */}
                            {operation && (operation.path || operation.filePath) && sandboxId && (
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => downloadFile(operation.path || operation.filePath || '')}
                                    className="h-6 px-2"
                                    title="下载文件"
                                >
                                    <Download className="h-3 w-3" />
                                </Button>
                            )}
                            {/* 下载按钮 - 当没有 sandboxId 但有文件内容时，使用内容下载 */}
                            {operation && !sandboxId && getDisplayContent(operation) && canDisplayContent(operation) && (
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => {
                                        const content = getDisplayContent(operation);
                                        if (content) {
                                            downloadFileContent(content, getFileName(operation.path));
                                        }
                                    }}
                                    className="h-6 px-2"
                                    title="下载文件内容"
                                >
                                    <Download className="h-3 w-3" />
                                </Button>
                            )}
                            {/* 状态指示器 */}
                            {operation && !operation.isLoading && (
                                <span
                                    className={cn(
                                        'text-xs flex items-center',
                                        operation.isSuccess
                                            ? 'text-emerald-500 dark:text-emerald-400'
                                            : 'text-rose-500 dark:text-rose-400',
                                    )}
                                >
                                    <span className="h-1.5 w-1.5 rounded-full mr-1.5 bg-current"></span>
                                    {operation.isSuccess ? '成功' : '失败'}
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="flex-1 bg-white/60 overflow-y-auto">
                        <div className="h-full text-zinc-800 dark:text-zinc-200 space-y-3">
                            {operation && (
                                <>
                                    {/* str_replace 操作的特殊显示 */}
                                    <RenderStrReplaceContent operation={operation} />

                                    {/* 批量写入文件列表 */}
                                    {renderBatchWriteFiles(operation)}

                                    {/* 文件内容显示 */}
                                    <RenderFileContent operation={operation} sandboxId={sandboxId || ""} />

                                    {/* 操作结果显示 */}
                                    {/* {renderResultContent(operation)} */}

                                    {operation.isLoading && (
                                        <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
                                            <CircleDashed className="h-3 w-3 text-blue-400 animate-spin" />
                                            <span className="tracking-wide">文件操作执行中...</span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
});
