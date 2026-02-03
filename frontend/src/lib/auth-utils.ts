import crypto from 'crypto';

export class AuthUtils {
    private static readonly CHARSET_UTF8 = 'utf8';
    private static readonly ALGORITHM_NAME = 'hmacsha256';
    private static readonly DIGEST_NAME = 'SHA-256';
    private static readonly AUTH_KEY = 'Authorization';
    private static readonly DATE_FORMAT_PATTERN = 'EEE, dd MMM yyyy HH:mm:ss z';

    /**
     * 生成 API网关鉴权的 HTTP POST 请求参数URL
     */
    public static assemblePostRequestUrl(requestUrl: string, apiKey: string, apiSecret: string): string {
        return this.assembleRequestUrl('POST', requestUrl, apiKey, apiSecret);
    }

    /**
     * 生成 API网关鉴权的 HTTP GET 请求参数URL
     */
    public static assembleGetRequestUrl(requestUrl: string, apiKey: string, apiSecret: string): string {
        return this.assembleRequestUrl('GET', requestUrl, apiKey, apiSecret);
    }

    /**
     * 生成 API网关鉴权的 HTTP 请求参数URL
     */
    public static assembleRequestUrl(httpMethod: string, requestUrl: string, apiKey: string, apiSecret: string): string {
        const authorizationData = this.assemble(httpMethod, requestUrl, apiKey, apiSecret, "");

        try {
            const authBase = Buffer.from(authorizationData.authorization, this.CHARSET_UTF8).toString('base64');
            const url = new URL(requestUrl);
            const hasQuery = url.search && url.search.length > 0;
            const separator = hasQuery ? '&' : '?';

            const authUrl = `${requestUrl}${separator}${this.AUTH_KEY.toLowerCase()}=${encodeURIComponent(authBase)}&host=${encodeURIComponent(authorizationData.host)}&date=${this.convertDate(authorizationData.date)}`;

            // console.debug('assembleRequestUrl:', authUrl);
            return authUrl;
        } catch (error) {
            console.error('assemble RequestUrl error', error);
            throw new Error('Failed to assemble request URL');
        }
    }

    /**
     * 生成 API网关鉴权的 HTTP请求 Header 字典
     */
    public static assembleAuthorizationHeaders(httpMethod: string, requestUrl: string, apiKey: string, apiSecret: string, body?: string): Record<string, string> {
        const authorizationData = this.assemble(httpMethod, requestUrl, apiKey, apiSecret, body);
        return authorizationData.getHeader();
    }

    private static assemble(httpMethod: string, requestUrl: string, apiKey: string, apiSecret: string, body?: string): AuthorizationData {
        if (!requestUrl) {
            throw new Error('requestUrl is empty.');
        }
        if (!apiKey) {
            throw new Error('apiKey is empty.');
        }
        if (!apiSecret) {
            throw new Error('apiSecret is empty.');
        }

        try {
            const httpRequestUrl = requestUrl.replace('ws://', 'http://').replace('wss://', 'https://');
            const url = new URL(httpRequestUrl);
            const date = this.formatDate(new Date());

            const sha = this.getSignature(url.hostname, date, this.getRequestLine(httpMethod, url.pathname), apiSecret);

            let digest: string | null = null;
            if (body) {
                digest = this.signBody(body);
            }

            const authorization = `hmac api_key="${apiKey}", algorithm="hmac-sha256", headers="host date request-line${digest ? ' digest' : ''}", signature="${sha}"`;

            const authorizationData = new AuthorizationData();
            authorizationData.setDate(date).setHost(url.hostname).setAuthorization(authorization).setDigest(digest);

            // console.debug('authorizationData:', authorizationData.toString());
            return authorizationData;
        } catch (error) {
            console.error('assemble AuthorizationData error', error);
            throw new Error('Failed to assemble authorization data');
        }
    }

    public static getRequestLine(method: string, path: string): string {
        return `${method.toUpperCase()} ${path} HTTP/1.1`;
    }

    /**
     * 生成签名
     */
    public static getSignature(host: string, date: string, requestLine: string, apiSecret: string): string {
        if (!host) {
            throw new Error('host is empty.');
        }
        if (!date) {
            throw new Error('date is empty.');
        }
        if (!requestLine) {
            throw new Error('requestLine is empty.');
        }
        if (!apiSecret) {
            throw new Error('apiSecret is empty.');
        }

        try {
            const url = new URL(`skynet://${host}`);
            const builder = `host: ${url.host}\ndate: ${date}\n${requestLine}`;

            // console.debug('\n--signing string:---------------------------------------\n{}\n--signing string:---------------------------------------', builder);

            const hmac = crypto.createHmac('sha256', apiSecret);
            hmac.update(Buffer.from(builder, this.CHARSET_UTF8));
            const signature = hmac.digest('base64');

            // console.debug('signature:', signature);
            return signature;
        } catch (error) {
            console.error('getSignature error', error);
            throw new Error('Failed to generate signature');
        }
    }

    public static signBody(body: string): string {
        if (!body) {
            throw new Error('body is empty.');
        }
        try {
            return this.signBodyBytes(Buffer.from(body, this.CHARSET_UTF8));
        } catch (error) {
            console.error('Body签名失败：', error);
            throw error;
        }
    }

    public static signBodyBytes(body: Buffer): string {
        if (!body || body.length === 0) {
            throw new Error('body is empty.');
        }
        try {
            const hash = crypto.createHash('sha256');
            hash.update(body);
            const digest = hash.digest('base64');
            return digest;
        } catch (error) {
            console.error('Body签名失败：', error);
            throw error;
        }
    }

    private static convertDate(date: string): string {
        return date.replaceAll(" ", "+").replaceAll(",", "%2C").replaceAll(":", "%3A")
    }

    private static formatDate(date: Date): string {
        const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        const weekday = weekdays[date.getUTCDay()];
        const day = date.getUTCDate().toString().padStart(2, '0');
        const month = months[date.getUTCMonth()];
        const year = date.getUTCFullYear();
        const hours = date.getUTCHours().toString().padStart(2, '0');
        const minutes = date.getUTCMinutes().toString().padStart(2, '0');
        const seconds = date.getUTCSeconds().toString().padStart(2, '0');

        return `${weekday}, ${day} ${month} ${year} ${hours}:${minutes}:${seconds} GMT`;
    }
}

class AuthorizationData {
    private _date: string = '';
    private _host: string = '';
    private _authorization: string = '';
    private _digest: string | null = null;

    setDate(date: string): AuthorizationData {
        this._date = date;
        return this;
    }

    setHost(host: string): AuthorizationData {
        this._host = host;
        return this;
    }

    setAuthorization(authorization: string): AuthorizationData {
        this._authorization = authorization;
        return this;
    }

    setDigest(digest: string | null): AuthorizationData {
        this._digest = digest;
        return this;
    }

    get date(): string {
        return this._date;
    }

    get host(): string {
        return this._host;
    }

    get authorization(): string {
        return this._authorization;
    }

    get digest(): string | null {
        return this._digest;
    }

    getHeader(): Record<string, string> {
        const headers: Record<string, string> = {
            'Host': this._host,
            'Date': this._date,
        };

        if (this._digest) {
            headers['Digest'] = `SHA-256=${this._digest}`;
        }
        headers['Authorization'] = this._authorization;

        return headers;
    }

    toString(): string {
        return `host=${this._host};date=${this._date};digest=${this._digest};authorization=${this._authorization};`;
    }
} 