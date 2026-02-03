import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse


class AuthUtils:
    """API网关鉴权工具类"""

    CHARSET_UTF8 = 'utf-8'
    ALGORITHM_NAME = 'hmacsha256'
    DIGEST_NAME = 'SHA-256'
    AUTH_KEY = 'Authorization'
    DATE_FORMAT_PATTERN = 'EEE, dd MMM yyyy HH:mm:ss z'

    @staticmethod
    def assemble_post_request_url(request_url: str, api_key: str, api_secret: str) -> str:
        """
        生成 API网关鉴权的 HTTP POST 请求参数URL
        """
        return AuthUtils.assemble_request_url('POST', request_url, api_key, api_secret)

    @staticmethod
    def assemble_get_request_url(request_url: str, api_key: str, api_secret: str) -> str:
        """
        生成 API网关鉴权的 HTTP GET 请求参数URL
        """
        return AuthUtils.assemble_request_url('GET', request_url, api_key, api_secret)

    @staticmethod
    def assemble_request_url(http_method: str, request_url: str, api_key: str, api_secret: str) -> str:
        """
        生成 API网关鉴权的 HTTP 请求参数URL
        """
        authorization_data = AuthUtils.assemble(http_method, request_url, api_key, api_secret, "")

        try:
            auth_base = base64.b64encode(authorization_data.authorization.encode(AuthUtils.CHARSET_UTF8)).decode(
                'utf-8')
            parsed_url = urlparse(request_url)
            has_query = bool(parsed_url.query)
            separator = '&' if has_query else '?'

            auth_url = f"{request_url}{separator}{AuthUtils.AUTH_KEY.lower()}={urllib.parse.quote(auth_base)}&host={urllib.parse.quote(authorization_data.host)}&date={AuthUtils.convert_date(authorization_data.date)}"

            print(f'DEBUG: assembleRequestUrl: {auth_url}')
            return auth_url
        except Exception as error:
            print(f'ERROR: assemble RequestUrl error: {error}')
            raise Exception('Failed to assemble request URL')

    @staticmethod
    def assemble_authorization_headers(http_method: str, request_url: str, api_key: str, api_secret: str,
                                       body: Optional[str] = None) -> Dict[str, str]:
        """
        生成 API网关鉴权的 HTTP请求 Header 字典
        """
        authorization_data = AuthUtils.assemble(http_method, request_url, api_key, api_secret, body)
        return authorization_data.get_header()

    @staticmethod
    def assemble(http_method: str, request_url: str, api_key: str, api_secret: str,
                 body: Optional[str] = None) -> 'AuthorizationData':
        """
        组装授权数据
        """
        if not request_url:
            raise Exception('requestUrl is empty.')
        if not api_key:
            raise Exception('apiKey is empty.')
        if not api_secret:
            raise Exception('apiSecret is empty.')

        try:
            # 将ws://和wss://替换为http://和https://
            http_request_url = request_url.replace('ws://', 'http://').replace('wss://', 'https://')
            parsed_url = urlparse(http_request_url)
            date = AuthUtils.format_date(datetime.utcnow())

            sha = AuthUtils.get_signature(parsed_url.hostname, date,
                                          AuthUtils.get_request_line(http_method, parsed_url.path), api_secret)

            digest = None
            if body:
                digest = AuthUtils.sign_body(body)

            authorization = f'hmac api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line{" digest" if digest else ""}", signature="{sha}"'

            authorization_data = AuthorizationData()
            authorization_data.set_date(date).set_host(parsed_url.hostname).set_authorization(authorization).set_digest(
                digest)

            print(f'DEBUG: authorizationData: {authorization_data.to_string()}')
            return authorization_data
        except Exception as error:
            print(f'ERROR: assemble AuthorizationData error: {error}')
            raise Exception('Failed to assemble authorization data')

    @staticmethod
    def get_request_line(method: str, path: str) -> str:
        """
        生成请求行
        """
        return f"{method.upper()} {path} HTTP/1.1"

    @staticmethod
    def get_signature(host: str, date: str, request_line: str, api_secret: str) -> str:
        """
        生成签名
        """
        if not host:
            raise Exception('host is empty.')
        if not date:
            raise Exception('date is empty.')
        if not request_line:
            raise Exception('requestLine is empty.')
        if not api_secret:
            raise Exception('apiSecret is empty.')

        try:
            # 构建签名字符串
            builder = f"host: {host}\ndate: {date}\n{request_line}"

            print(
                f'\n--signing string:---------------------------------------\n{builder}\n--signing string:---------------------------------------')

            # 使用HMAC-SHA256生成签名
            signature = hmac.new(
                api_secret.encode(AuthUtils.CHARSET_UTF8),
                builder.encode(AuthUtils.CHARSET_UTF8),
                hashlib.sha256
            ).digest()

            signature_b64 = base64.b64encode(signature).decode('utf-8')
            print(f'DEBUG: signature: {signature_b64}')
            return signature_b64
        except Exception as error:
            print(f'ERROR: getSignature error: {error}')
            raise Exception('Failed to generate signature')

    @staticmethod
    def sign_body(body: str) -> str:
        """
        对请求体进行签名
        """
        if not body:
            raise Exception('body is empty.')
        try:
            return AuthUtils.sign_body_bytes(body.encode(AuthUtils.CHARSET_UTF8))
        except Exception as error:
            print(f'ERROR: Body签名失败: {error}')
            raise error

    @staticmethod
    def sign_body_bytes(body: bytes) -> str:
        """
        对字节数据进行签名
        """
        if not body or len(body) == 0:
            raise Exception('body is empty.')
        try:
            hash_obj = hashlib.sha256()
            hash_obj.update(body)
            digest = base64.b64encode(hash_obj.digest()).decode('utf-8')
            return digest
        except Exception as error:
            print(f'ERROR: Body签名失败: {error}')
            raise error

    @staticmethod
    def convert_date(date: str) -> str:
        """
        转换日期格式用于URL编码
        """
        return date.replace(" ", "+").replace(",", "%2C").replace(":", "%3A")

    @staticmethod
    def format_date(date: datetime) -> str:
        """
        格式化日期为GMT格式
        """
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        weekday = weekdays[date.weekday()]
        day = f"{date.day:02d}"
        month = months[date.month - 1]
        year = date.year
        hours = f"{date.hour:02d}"
        minutes = f"{date.minute:02d}"
        seconds = f"{date.second:02d}"

        return f"{weekday}, {day} {month} {year} {hours}:{minutes}:{seconds} GMT"


class AuthorizationData:
    """授权数据类"""

    def __init__(self):
        self._date: str = ''
        self._host: str = ''
        self._authorization: str = ''
        self._digest: Optional[str] = None

    def set_date(self, date: str) -> 'AuthorizationData':
        self._date = date
        return self

    def set_host(self, host: str) -> 'AuthorizationData':
        self._host = host
        return self

    def set_authorization(self, authorization: str) -> 'AuthorizationData':
        self._authorization = authorization
        return self

    def set_digest(self, digest: Optional[str]) -> 'AuthorizationData':
        self._digest = digest
        return self

    @property
    def date(self) -> str:
        return self._date

    @property
    def host(self) -> str:
        return self._host

    @property
    def authorization(self) -> str:
        return self._authorization

    @property
    def digest(self) -> Optional[str]:
        return self._digest

    def get_header(self) -> Dict[str, str]:
        """
        获取HTTP头部字典
        """
        headers = {
            'Host': self._host,
            'Date': self._date,
        }

        if self._digest:
            headers['Digest'] = f'SHA-256={self._digest}'

        headers['Authorization'] = self._authorization
        return headers

    def to_string(self) -> str:
        """
        转换为字符串表示
        """
        return f"host={self._host};date={self._date};digest={self._digest};authorization={self._authorization};"


# 使用示例
if __name__ == "__main__":
    # 示例用法
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    request_url = "https://api.example.com/endpoint"

    try:
        # 生成GET请求URL
        get_url = AuthUtils.assemble_get_request_url(request_url, api_key, api_secret)
        print(f"GET URL: {get_url}")

        # 生成POST请求URL
        post_url = AuthUtils.assemble_post_request_url(request_url, api_key, api_secret)
        print(f"POST URL: {post_url}")

        # 生成请求头，一般不需要
        headers = AuthUtils.assemble_authorization_headers('POST', request_url, api_key, api_secret,
                                                           '{"data": "example"}')
        print(f"Headers: {headers}")

    except Exception as e:
        print(f"Error: {e}")
