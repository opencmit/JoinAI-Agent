import crypto from 'crypto';
import { v4 as uuidv4 } from 'uuid';

/**
 * AI Authentication Utils
 * Based on Python code for generating X-Server-Param, X-CurTime, X-CheckSum headers
 */
export class AIAuthUtils {
    /**
     * 生成AI鉴权签名头信息
     * Generates authentication headers for AI services
     * 
     * @param appid - Application ID
     * @param appkey - Application Key
     * @param capabilityname - Capability Name
     * @returns Authentication headers object
     */
    public static generateAuthHeaders(
        appid: string,
        appkey: string,
        capabilityname: string
    ): Record<string, string> {
        try {
            // 生成UUID (移除连字符)
            const uuid = this.generateUUID();

            // 设置请求头参数
            const serverParam = {
                appid: appid,
                csid: `${appid}${capabilityname}${uuid}`
            };

            // 当前时间戳
            const curTime = Math.floor(Date.now() / 1000).toString();

            // Base64编码服务器参数
            const xServerParamBase64 = this.base64Encode(
                JSON.stringify(serverParam, Object.keys(serverParam).sort())
            );

            // 生成MD5校验和
            const checksumString = `${appkey}${curTime}${xServerParamBase64}`;
            const checksum = this.generateMD5Hash(checksumString);

            // 返回认证头信息
            return {
                'X-Server-Param': xServerParamBase64,
                'X-CurTime': curTime,
                'X-CheckSum': checksum,
                'Content-Type': 'application/json; charset=utf-8'
            };
        } catch (error) {
            console.error('生成AI鉴权签名失败:', error);
            throw new Error('Failed to generate AI authentication headers');
        }
    }

    /**
     * 生成UUID (移除连字符)
     * Generate UUID without hyphens, similar to Python str(uuid.uuid4()).replace('-', '')
     */
    private static generateUUID(): string {
        return uuidv4().replace(/-/g, '');
    }

    /**
     * Base64编码
     * Encode string to base64
     */
    private static base64Encode(str: string): string {
        return Buffer.from(str, 'utf8').toString('base64');
    }

    /**
     * 生成MD5哈希
     * Generate MD5 hash equivalent to Python hashlib.md5().hexdigest()
     */
    private static generateMD5Hash(input: string): string {
        return crypto.createHash('md5').update(input, 'utf8').digest('hex');
    }

    /**
     * 生成完整的AI认证配置 (包含默认值示例)
     * Generate AI authentication configuration with default example values
     * 
     * @returns Authentication headers for AI entity recognition service
     */
    public static generateDefaultAuthHeaders(): Record<string, string> {
        const appid = "xxx";
        const appkey = "xxx";
        const capabilityname = "xxx";

        return this.generateAuthHeaders(appid, appkey, capabilityname);
    }
}
