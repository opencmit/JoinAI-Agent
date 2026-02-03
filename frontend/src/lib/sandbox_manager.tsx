"use server";
import { Sandbox as DesktopSandbox } from '@e2b/desktop';
import { Sandbox as CodeInterpreterSandbox } from '@e2b/code-interpreter';

// 定义AgentState类型
export interface AgentState {
    // copilotkit: { actions: any[] };
    // messages: any[];
    // logs: any[];
    e2b_sandbox_id?: string;
}

// 配置
const llmConfig = {
    E2B_API_KEY: process.env.E2B_API_KEY!,
};

/**
 * Sandbox管理器，负责创建和管理sandbox实例
 */
class SandboxManager {
    private apiKey: string;

    /**
     * 构造函数
     * @param domain Sandbox服务域名
     * @param debug 是否开启调试模式
     * @param apiKey E2B API密钥
     */
    constructor(
        apiKey: string = llmConfig.E2B_API_KEY
    ) {
        this.apiKey = apiKey;
        console.log("SandboxManager constructor", this.apiKey);
    }

    /**
     * 获取同步sandbox实例
     * 尝试连接到提供的sandbox ID；如果失败，则创建一个新的同步实例。
     * @param sandboxId 可选的sandbox ID，用于连接到现有实例
     * @returns Sandbox实例
     */
    async getDesktopSandbox(sandboxId?: string): Promise<DesktopSandbox | null> {
        let sbx: DesktopSandbox | null = null;

        if (sandboxId) {
            try {
                // 尝试连接到现有sandbox
                sbx = await DesktopSandbox.connect(sandboxId, {
                    apiKey: this.apiKey,
                    // display: ":0", // 自定义显示器设置 (默认为:0)
                    // resolution: [1280, 720], // 自定义分辨率
                    // dpi: 96, // 自定义DPI
                });
            } catch (e) {
                console.error(`连接到现有同步sandbox失败: ${e}`);
                console.trace(e);
            }
        }

        return sbx;
    }

    /**
     * 获取异步sandbox实例
     * 尝试连接到提供的sandbox ID；如果失败，则创建一个新的异步实例。
     * @param sandboxId 可选的sandbox ID，用于连接到现有实例
     * @returns AsyncSandbox实例
     */
    async getCodeInterpreterSandbox(sandboxId?: string): Promise<CodeInterpreterSandbox | null> {
        let sbx: CodeInterpreterSandbox | null = null;

        if (sandboxId) {
            try {
                // 尝试连接到现有sandbox
                sbx = await CodeInterpreterSandbox.connect(sandboxId, {
                    apiKey: this.apiKey,
                });
            } catch (e) {
                console.error(`连接到现有CodeInterpreterSandbox失败: ${e}`);
                console.trace(e);
            }
        }

        return sbx;
    }

    // /**
    //  * 创建新的异步sandbox实例
    //  * @returns AsyncSandbox实例
    //  */
    // private async _createNewSandbox(): Promise<DesktopSandbox> {
    //     return await DesktopSandbox.create({
    //         domain: this.domain,
    //         debug: this.debug,
    //         apiKey: this.apiKey,
    //     });
    // }

    // /**
    //  * 创建新的同步sandbox实例
    //  * @returns DesktopSandbox实例
    //  */
    // private async _createNewSandboxSync(): Promise<DesktopSandbox> {
    //     return await DesktopSandbox.create({
    //         domain: this.domain,
    //         debug: this.debug,
    //         apiKey: this.apiKey,
    //         display: ":0", // 自定义显示器设置 (默认为:0)
    //         resolution: [1280, 720], // 自定义分辨率
    //         dpi: 96, // 自定义DPI
    //     });
    // }
}

// 创建默认实例
const sbxManager = new SandboxManager();
export async function getVNCUrl(sandboxId: string) {
    const sandbox = await sbxManager.getDesktopSandbox(sandboxId);
    if (!sandbox) {
        return null;
    }
    // Start the stream
    console.log("sandbox?.isRunning", await sandbox?.isRunning());
    // if (!sandbox.stream) {
    //     await sandbox.stream.start();
    // }
    try {
        await sandbox.stream.start();
    } catch (e) {
        console.warn('启动VNC流失败:', e);
    }
    return sandbox?.stream.getUrl();
}


export async function getFileContent(sandboxId: string, filePath: string, returnType: 'text' | 'bytes' | 'blob' | 'stream' = 'text'): Promise<string | Uint8Array | Blob | ReadableStream<Uint8Array> | null> {
    const sandbox = await sbxManager.getCodeInterpreterSandbox(sandboxId);
    if (!sandbox) {
        return null;
    }
    if (!await sandbox.files.exists(filePath)) {
        return null;
    }
    switch (returnType) {
        case 'text':
            return await sandbox.files.read(filePath, { format: 'text' });
        case 'bytes':
            return await sandbox.files.read(filePath, { format: 'bytes' });
        case 'blob':
            return await sandbox.files.read(filePath, { format: 'blob' });
        case 'stream':
            return await sandbox.files.read(filePath, { format: 'stream' });
        default:
            return null;
    }
}

export async function getDownloadUrl(sandboxId: string, filePath: string) {
    const sandbox = await sbxManager.getCodeInterpreterSandbox(sandboxId);
    if (!sandbox) {
        return null;
    }
    if (!await sandbox.files.exists(filePath)) {
        return null;
    }
    return sandbox.downloadUrl(filePath);
}
