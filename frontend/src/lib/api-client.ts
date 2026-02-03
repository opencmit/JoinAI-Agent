"use client"

import { CreateThread, ListNamespaceOptions, ListRuns, SearchAssistant, SearchItemsOptions, SearchThread, SearchStoreItem, StoreItem } from "@/types/langgraph";


// API客户端配置
export interface APIConfig {
    baseURL?: string;
    timeout?: number;
    headers?: Record<string, string>;
}

// API响应格式
export interface GeneralAPIResponse<T = any> {
    success: boolean;
    message: string;
    data: T;
}

export interface SCPAPIResponse<T = any> {
    success: boolean;
    message?: string;
    data?: T;
    count?: number;
    pageNo?: number;
    pageSize?: number;
    pageCount?: number;
    startRow?: number;
    endRow?: number;
}

export interface JuZhiAPIResponse<T = any> {
    code: number;
    message: string;
    data: T;
}

/**
 * 统一的API客户端类
 */
export class APIClient {
    private prefix: string;

    constructor(prefix: string = '') {
        if (prefix) {
            this.prefix = prefix;
        } else {
            this.prefix = '';
        }
    }

    private withPrefix(path: string) {
        // 避免重复斜杠
        if (path.startsWith('/')) {
            return `${this.prefix}${path}`;
        }
        return `${this.prefix}/${path}`;
    }

    /**
     * 获取沙箱文件下载URL
     * @param path 文件路径
     * @param useUrlParams 是否使用URL参数方式（默认false，使用请求头方式）
     * @returns 下载URL
     */
    getSandboxFileDownloadUrl(sandboxId: string, path: string): string {
        const baseUrl = this.withPrefix(`/api/file/download`);

        // 构建URL参数
        const urlParams = new URLSearchParams();
        urlParams.append('sandboxId', encodeURIComponent(sandboxId));
        urlParams.append('path', encodeURIComponent(path));

        return `${baseUrl}?${urlParams.toString()}`;
    }

    /**
     * 下载沙箱文件
     * @param path 文件路径
     * @returns Promise<Blob> - 文件二进制数据
     */
    async secureDownloadSandboxFile(sandboxId: string, path: string): Promise<Blob> {
        try {
            // 构建请求头
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store'
            };

            // 发起安全请求 - 同时传递URL参数和安全头
            const response = await fetch(this.withPrefix(`/api/file/download?sandboxId=${sandboxId}&path=${encodeURIComponent(path)}`), {
                method: 'GET',
                headers
            });

            if (!response.ok) {
                // 尝试解析错误响应
                try {
                    const errorData = await response.json();
                    throw new Error(`下载失败: ${errorData.error || response.statusText}`);
                } catch {
                    throw new Error(`下载失败: ${response.status} ${response.statusText}`);
                }
            }

            return await response.blob();

        } catch (error: any) {
            console.error('文件下载异常:', error);
            throw new Error(`文件下载失败: ${error.message}`);
        }
    }

    /**
     * 创建LangGraph会话
     */
    async createLangGraphThread(data: CreateThread): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/thread/create'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * 获取LangGraph助手列表
     */
    async getLangGraphAssistantList(data: SearchAssistant): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/assistant/search'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * 删除LangGraph助手
     */
    async deleteLangGraphAssistant(assistantId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/assistant/delete`), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                assistantId
            }),
        });
        return response.json();
    }

    /**
     * 获取LangGraph会话列表
     */
    async getLangGraphThreadList(data: SearchThread): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/thread/list'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * 获取LangGraph会话状态
     */
    async getLangGraphThreadState(threadId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/thread/get?threadId=${threadId}`), {
            method: 'GET',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
        });
        return response.json();
    }

    /**
     * 删除LangGraph会话
     */
    async deleteLangGraphThread(threadId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/thread/delete?threadId=${threadId}`), {
            method: 'GET',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
        });
        return response.json();
    }

    /**
     * 更新LangGraph会话
     */
    async updateLangGraphThread(threadId: string, data: Record<string, any>): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/thread/update?threadId=${threadId}`), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * 取消LangGraph会话
     */
    async cancelLangGraphThread(threadId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/runs/cancel?threadId=${threadId}`), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
        });
        return response.json();
    }

    /**
     * 获取LangGraph会话运行列表
     */
    async getLangGraphRunList(threadId: string, data: ListRuns): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/runs/list?threadId=${threadId}`), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * 取消LangGraph会话
     */
    async cancelLangGraphRun(threadId: string, runId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/runs/cancel?threadId=${threadId}&runId=${runId}`), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
        });
        return response.json();
    }

    /**
     * 删除LangGraph会话运行
     */
    async deleteLangGraphRun(threadId: string, runId: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/langgraph/runs/delete?threadId=${threadId}&runId=${runId}`), {
            method: 'GET',
        });
        return response.json();
    }

    /**
     * 获取LangGraph存储列表
     */
    async getLangGraphStoreList(namespace: string[], key: string): Promise<GeneralAPIResponse<StoreItem[]>> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/list-namespace'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                namespace,
                key
            }),
        });
        return response.json();
    }

    /**
     * 获取LangGraph存储搜索列表
     */
    async searchLangGraphStoreList(namespacePrefix: string[], searchOptions: SearchItemsOptions): Promise<GeneralAPIResponse<{ items: SearchStoreItem[] }>> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/search'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                namespacePrefix,
                searchOptions
            }),
        });
        return response.json();
    }

    /**
     * 获取LangGraph store
     */
    async getLangGraphStore(namespace: string[], key: string): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/get'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                namespace,
                key
            }),
        });
        return response.json();
    }

    /**
     * 存储或更新LangGraph store
     */
    async putLangGraphStoreList(namespace: string[], key: string, value: Record<string, any>): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/put'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                namespace,
                key,
                value
            }),
        });
        return response.json();
    }

    /**
     * 删除LangGraph store
     */
    async deleteLangGraphStoreList(namespace: string[], key: string): Promise<any> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/delete'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                namespace,
                key
            }),
        });
        return response.json();
    }

    /**
     * 获取LangGraph namespace列表
     */
    async getLangGraphStoreNamespaceList(data: ListNamespaceOptions): Promise<GeneralAPIResponse<{ namespaces: string[][] }>> {
        const response = await fetch(this.withPrefix('/api/langgraph/store/list-namespace'), {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }

    async getThreadTitle(message: string): Promise<any> {
        const response = await fetch(this.withPrefix(`/api/model/title`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store'
            },
            body: JSON.stringify({
                message: message
            }),
        });
        return response.json();
    }

    /**
     * 文件上传接口
     * @param data 文件数据
     * @returns 上传结果
     */
    async fileUpload(data: FormData): Promise<GeneralAPIResponse<{ saveName: string, savePath: string }>> {
        const response = await fetch(this.withPrefix(`/api/file/upload`), {
            method: 'POST',
            body: data,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }
}

// 导出基础API客户端实例
export const apiClient = new APIClient(""); 