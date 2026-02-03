#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import time
import random
import re
import datetime
import logging
from typing import Dict, Any, Optional, List
import os
import uuid
import base64
from abc import ABC, abstractmethod
import asyncio
from threading import Thread
import queue
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# 加载当前文件夹的.env文件
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

# LangChain依赖（可选，需要时安装）
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置Flask以正确处理中文字符
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 服务器配置
SERVER_PORT = 18585
SERVER_HOST = '0.0.0.0'

def json_response(data: Dict[str, Any], status_code: int = 200) -> Response:
    """
    创建带有正确中文编码的JSON响应
    
    Args:
        data: 要返回的数据
        status_code: HTTP状态码
    
    Returns:
        Response: Flask响应对象
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        json_str,
        status=status_code,
        mimetype='application/json; charset=utf-8',
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )

# A2A智能体会话存储
sessions: Dict[str, Dict] = {}

# 天气数据模拟（用于WeatherAgent）
WEATHER_DATA = {
    "北京": {"temperature": "15°C", "weather": "晴天", "humidity": "45%", "wind": "微风"},
    "上海": {"temperature": "18°C", "weather": "多云", "humidity": "60%", "wind": "小风"},
    "广州": {"temperature": "25°C", "weather": "小雨", "humidity": "80%", "wind": "微风"},
    "深圳": {"temperature": "26°C", "weather": "阴天", "humidity": "75%", "wind": "无风"},
    "杭州": {"temperature": "20°C", "weather": "晴天", "humidity": "50%", "wind": "微风"},
    "成都": {"temperature": "22°C", "weather": "雾霾", "humidity": "70%", "wind": "小风"},
}

class BaseA2AAgent(ABC):
    """A2A智能体基础抽象类（Flask版本）"""
    
    def __init__(self, name: str, description: str):
        """
        初始化A2A智能体
        
        Args:
            name: 智能体名称
            description: 智能体描述
        """
        self.name = name
        self.description = description
        self.agent_id = self.__class__.agent_id
        self.keywords = self.__class__.keywords
        self.llm_client = self._create_llm_client() if LLM_AVAILABLE else None
        
        logger.info(f"🤖 初始化智能体: {self.name}")
        logger.info(f"   ID: {self.agent_id}")
        logger.info(f"   描述: {self.description}")
        logger.info(f"   关键词: {', '.join(self.keywords)}")
        
    def _create_llm_client(self) -> Optional[ChatOpenAI]:
        """创建LLM客户端（仅在LangChain可用时）"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.getenv("BASE_LLM", "openai/gpt-oss-20b")
            
            if not api_key:
                logger.warning("⚠️ OPENAI_API_KEY 未设置，将使用模拟响应")
                return None
            
            client = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=0.7
            )
            
            logger.info(f"✅ LLM客户端创建成功: {model}")
            return client
            
        except Exception as e:
            logger.error(f"❌ LLM客户端创建失败: {str(e)}")
            return None
    
    def _process_with_llm(self, text: str) -> dict:
        """使用LLM处理消息的同步包装"""
        try:
            if not self.llm_client:
                return self._get_basic_response(text)
            
            system_prompt = self._get_system_prompt()
            
            # 使用ThreadPoolExecutor执行异步LLM调用
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._call_llm_sync, system_prompt, text)
                response_text = future.result(timeout=300)
            
            return {
                "type": "text",
                "response": response_text,
                "agent_name": self.name,
                "agent_id": self.agent_id,
                "llm_used": True
            }
            
        except Exception as e:
            logger.error(f"❌ LLM处理失败: {str(e)}")
            return self._get_basic_response(text)
    
    def _call_llm_sync(self, system_prompt: str, user_message: str) -> str:
        """同步调用LLM"""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm_client.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"❌ LLM同步调用失败: {str(e)}")
            return self._get_fallback_response(user_message)
    
    def _get_basic_response(self, text: str) -> dict:
        """获取基本响应格式"""
        return {
            "type": "text",
            "response": self._get_fallback_response(text),
            "agent_name": self.name,
            "agent_id": self.agent_id,
            "llm_used": False
        }
    
    def process_message(self, text: str) -> dict:
        """处理用户消息（同步版本）"""
        logger.info(f"🎯 {self.name} 开始处理消息: {text}")
        
        if self.llm_client and LLM_AVAILABLE:
            # 使用LLM处理
            result = self._process_with_llm(text)
        else:
            # 使用回退响应
            result = self._get_basic_response(text)
        
        logger.info(f"✅ {self.name} 消息处理完成")
        return result
    
    @abstractmethod
    def _get_fallback_response(self, user_message: str) -> str:
        """获取备用响应（LLM不可用时）"""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """获取智能体专用的系统提示词"""
        pass

class MCPToolResult:
    """MCP工具执行结果类"""
    
    def __init__(self, content: str, status: bool = True, type: str = "text", error_msg: str = ""):
        """
        初始化MCP工具执行结果
        
        Args:
            content: 返回内容
            status: 执行状态，True为成功，False为失败
            type: 返回数据类型，默认为"text"
            error_msg: 失败原因，仅在status为False时使用
        """
        self.content = content
        self.status = status
        self.type = type
        self.error_msg = error_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "type": self.type,
            "content": self.content,
            "status": self.status
        }
        if not self.status and self.error_msg:
            result["errorMsg"] = self.error_msg
        return result

class MCPToolRegistry:
    """MCP工具注册表类"""
    
    def __init__(self):
        """初始化工具注册表"""
        self.tools = {}
        self._register_default_tools()
    
    def register_tool(self, tool_id: str, handler_func, description: str = ""):
        """
        注册工具
        
        Args:
            tool_id: 工具唯一标识符
            handler_func: 工具处理函数
            description: 工具描述
        """
        self.tools[tool_id] = {
            'handler': handler_func,
            'description': description,
            'registered_at': datetime.datetime.now().isoformat()
        }
        logger.info(f"工具已注册: {tool_id} - {description}")
    
    def get_tool(self, tool_id: str) -> Optional[callable]:
        """获取工具处理函数"""
        tool_info = self.tools.get(tool_id)
        return tool_info['handler'] if tool_info else None
    
    def list_tools(self) -> Dict[str, Any]:
        """获取所有已注册工具的信息"""
        return {
            tool_id: {
                'description': tool_info['description'],
                'registered_at': tool_info['registered_at']
            }
            for tool_id, tool_info in self.tools.items()
        }
    
    def _register_default_tools(self):
        """注册默认工具集合"""
        # Hello World 工具
        self.register_tool(
            "hello_world",
            self._handle_hello_world,
            "Hello World问候工具，可以自定义问候语言和对象"
        )
        
        # 计算器工具
        self.register_tool(
            "calculator",
            self._handle_calculator,
            "数学计算器工具，支持基本四则运算和数学函数"
        )
        
        # 文本处理工具
        self.register_tool(
            "text_processor",
            self._handle_text_processor,
            "文本处理工具，支持大小写转换、字符统计、去除空白等操作"
        )
        
        # 随机数生成器
        self.register_tool(
            "random_generator",
            self._handle_random_generator,
            "随机数生成器，可生成指定范围内的随机整数或浮点数"
        )
        
        # 时间工具
        self.register_tool(
            "time_tool",
            self._handle_time_tool,
            "时间查询工具，提供当前时间、时间格式转换等功能"
        )
        
        # 回显工具
        self.register_tool(
            "echo_tool",
            self._handle_echo_tool,
            "回显工具，用于测试参数传递和响应格式"
        )
    
    def _handle_hello_world(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理Hello World工具请求"""
        try:
            name = arguments.get('name', 'World')
            language = arguments.get('language', 'cn')
            
            greetings = {
                'cn': f"你好，{name}！",
                'en': f"Hello, {name}!",
                'jp': f"こんにちは、{name}！",
                'kr': f"안녕하세요, {name}!",
                'fr': f"Bonjour, {name}!",
                'de': f"Hallo, {name}!",
                'es': f"¡Hola, {name}!",
                'it': f"Ciao, {name}!"
            }
            
            greeting = greetings.get(language, greetings['cn'])
            
            result_content = f"""🌟 MCP Hello World 工具

{greeting}

📋 请求信息:
- 姓名: {name}
- 语言: {language}
- 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚀 这是一个MCP测试工具，用于验证工具调用接口的正确性。"""
            
            return MCPToolResult(content=result_content)
            
        except Exception as e:
            logger.error(f"Hello World工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"Hello World工具执行失败: {str(e)}"
            )
    
    def _handle_calculator(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理计算器工具请求"""
        try:
            expression = arguments.get('expression', '')
            operation = arguments.get('operation', '')
            a = arguments.get('a')
            b = arguments.get('b')
            
            if expression:
                # 简单安全的表达式计算
                try:
                    # 仅允许数字、基本操作符和括号
                    import re
                    if re.match(r'^[0-9+\-*/().\s]+$', expression):
                        result = eval(expression)
                        content = f"""🧮 计算器工具结果

📝 表达式: {expression}
📊 结果: {result}
⏰ 计算时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                        return MCPToolResult(content=content)
                    else:
                        return MCPToolResult(
                            content="",
                            status=False,
                            type="error",
                            error_msg="表达式包含不允许的字符"
                        )
                except Exception as e:
                    return MCPToolResult(
                        content="",
                        status=False,
                        type="error",
                        error_msg=f"表达式计算错误: {str(e)}"
                    )
            
            elif operation and a is not None and b is not None:
                # 操作符计算模式
                a = float(a)
                b = float(b)
                
                operations = {
                    'add': (lambda x, y: x + y, '+'),
                    'subtract': (lambda x, y: x - y, '-'),
                    'multiply': (lambda x, y: x * y, '*'),
                    'divide': (lambda x, y: x / y if y != 0 else None, '/'),
                    'power': (lambda x, y: x ** y, '^'),
                    'modulo': (lambda x, y: x % y if y != 0 else None, '%')
                }
                
                if operation in operations:
                    func, symbol = operations[operation]
                    result = func(a, b)
                    
                    if result is None:
                        return MCPToolResult(
                            content="",
                            status=False,
                            type="error",
                            error_msg="除数不能为零"
                        )
                    
                    content = f"""🧮 计算器工具结果

📝 计算: {a} {symbol} {b}
📊 结果: {result}
⏰ 计算时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                    
                    return MCPToolResult(content=content)
                else:
                    return MCPToolResult(
                        content="",
                        status=False,
                        type="error",
                        error_msg=f"不支持的操作: {operation}"
                    )
            
            else:
                return MCPToolResult(
                    content="",
                    status=False,
                    type="error",
                    error_msg="请提供表达式(expression)或操作参数(operation, a, b)"
                )
                
        except Exception as e:
            logger.error(f"计算器工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"计算器工具执行失败: {str(e)}"
            )
    
    def _handle_text_processor(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理文本处理工具请求"""
        try:
            text = arguments.get('text', '')
            operation = arguments.get('operation', 'info')
            
            if not text:
                return MCPToolResult(
                    content="",
                    status=False,
                    type="error",
                    error_msg="请提供要处理的文本内容"
                )
            
            result_lines = []
            result_lines.append("📝 文本处理工具结果\n")
            result_lines.append(f"📄 原始文本: {text[:100]}{'...' if len(text) > 100 else ''}\n")
            
            if operation == 'info' or operation == 'all':
                # 文本信息统计
                result_lines.extend([
                    "📊 文本统计信息:",
                    f"   - 字符总数: {len(text)}",
                    f"   - 字符数(不含空格): {len(text.replace(' ', ''))}",
                    f"   - 单词数: {len(text.split())}",
                    f"   - 行数: {len(text.splitlines())}",
                    ""
                ])
            
            if operation == 'upper' or operation == 'all':
                result_lines.extend([
                    f"🔤 大写转换: {text.upper()}",
                    ""
                ])
            
            if operation == 'lower' or operation == 'all':
                result_lines.extend([
                    f"🔡 小写转换: {text.lower()}",
                    ""
                ])
            
            if operation == 'reverse' or operation == 'all':
                result_lines.extend([
                    f"🔄 反转文本: {text[::-1]}",
                    ""
                ])
            
            result_lines.append(f"⏰ 处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return MCPToolResult(content="\n".join(result_lines))
            
        except Exception as e:
            logger.error(f"文本处理工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"文本处理工具执行失败: {str(e)}"
            )
    
    def _handle_random_generator(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理随机数生成器工具请求"""
        try:
            type_param = arguments.get('type', 'int')
            min_val = arguments.get('min', 1)
            max_val = arguments.get('max', 100)
            count = arguments.get('count', 1)
            
            # 参数验证
            if count <= 0 or count > 1000:
                return MCPToolResult(
                    content="",
                    status=False,
                    type="error",
                    error_msg="count参数必须在1-1000之间"
                )
            
            results = []
            
            if type_param == 'int':
                for _ in range(count):
                    results.append(random.randint(min_val, max_val))
            elif type_param == 'float':
                for _ in range(count):
                    results.append(round(random.uniform(min_val, max_val), 6))
            elif type_param == 'choice':
                choices = arguments.get('choices', ['A', 'B', 'C'])
                for _ in range(count):
                    results.append(random.choice(choices))
            else:
                return MCPToolResult(
                    content="",
                    status=False,
                    type="error",
                    error_msg="不支持的随机数类型，支持: int, float, choice"
                )
            
            content = f"""🎲 随机数生成器结果

⚙️ 生成参数:
   - 类型: {type_param}
   - 范围: {min_val} - {max_val}
   - 数量: {count}

🎯 生成结果:
{', '.join(map(str, results))}

⏰ 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            return MCPToolResult(content=content)
            
        except Exception as e:
            logger.error(f"随机数生成器工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"随机数生成器工具执行失败: {str(e)}"
            )
    
    def _handle_time_tool(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理时间工具请求"""
        try:
            operation = arguments.get('operation', 'current')
            format_str = arguments.get('format', '%Y-%m-%d %H:%M:%S')
            
            now = datetime.datetime.now()
            
            content_lines = ["⏰ 时间工具结果\n"]
            
            if operation == 'current' or operation == 'all':
                content_lines.extend([
                    f"📅 当前时间: {now.strftime(format_str)}",
                    f"📊 时间戳: {int(now.timestamp())}",
                    f"🗓️ 星期: {now.strftime('%A')}",
                    f"📆 年份: {now.year}",
                    f"📅 月份: {now.month}",
                    f"📆 日期: {now.day}",
                    f"⏰ 小时: {now.hour}",
                    f"⏱️ 分钟: {now.minute}",
                    f"⏲️ 秒数: {now.second}",
                    ""
                ])
            
            if operation == 'format' or operation == 'all':
                formats = {
                    'ISO 8601': now.isoformat(),
                    'RFC 2822': now.strftime('%a, %d %b %Y %H:%M:%S'),
                    '中文格式': now.strftime('%Y年%m月%d日 %H时%M分%S秒'),
                    'Unix时间戳': str(int(now.timestamp())),
                    '简短日期': now.strftime('%Y-%m-%d'),
                    '简短时间': now.strftime('%H:%M:%S')
                }
                
                content_lines.append("🎨 格式化选项:")
                for name, formatted in formats.items():
                    content_lines.append(f"   - {name}: {formatted}")
                content_lines.append("")
            
            content_lines.append(f"🌐 时区: 本地时间")
            
            return MCPToolResult(content="\n".join(content_lines))
            
        except Exception as e:
            logger.error(f"时间工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"时间工具执行失败: {str(e)}"
            )
    
    def _handle_echo_tool(self, arguments: Dict[str, Any]) -> MCPToolResult:
        """处理回显工具请求"""
        try:
            content = f"""🔄 回显工具结果

📦 接收到的参数:
{json.dumps(arguments, ensure_ascii=False, indent=2)}

📊 参数统计:
   - 参数数量: {len(arguments)}
   - 参数类型: {', '.join(type(v).__name__ for v in arguments.values())}

⏰ 处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 这是一个回显工具，用于测试参数传递的正确性。"""
            
            return MCPToolResult(content=content)
            
        except Exception as e:
            logger.error(f"回显工具执行失败: {str(e)}")
            return MCPToolResult(
                content="",
                status=False,
                type="error",
                error_msg=f"回显工具执行失败: {str(e)}"
            )

class WeatherAgent(BaseA2AAgent):
    """天气智能体 - 专业天气查询和预报服务"""
    
    agent_id = "weather-agent"
    keywords = ["天气", "气温", "降雨", "晴天", "下雨", "temperature", "weather", "气候", "预报"]
    
    def __init__(self):
        super().__init__(
            name="天气助手",
            description="我是专业的天气查询和预报智能体，可以为您提供准确的天气信息和气象分析"
        )
    
    def _get_system_prompt(self) -> str:
        return f"""你是一位专业的天气预报专家和气象分析师。

专业能力:
- 天气数据查询和分析
- 气象趋势预测
- 天气状况专业解读
- 多城市天气对比

可用城市数据: {', '.join(WEATHER_DATA.keys())}

天气数据库:
{json.dumps(WEATHER_DATA, ensure_ascii=False, indent=2)}

回答要求:
1. 使用专业的气象术语
2. 提供详细的天气分析
3. 包含实用的生活建议
4. 如果用户询问的城市在数据库中，使用真实数据
5. 保持专业、友好的语调
6. 用中文回答

请为用户提供专业的天气服务。"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        # 从用户消息中提取城市
        for city, data in WEATHER_DATA.items():
            if city in user_message:
                return f"""🌤️ {city}今天的天气情况：

🌡️ **温度**: {data['temperature']}
☁️ **天气**: {data['weather']} 
💧 **湿度**: {data['humidity']}
🌪️ **风力**: {data['wind']}

📊 **专业分析**: 根据当前气象数据，{city}今天{data['weather']}，温度适中，适合外出活动。

💡 **生活建议**: 建议根据天气情况适当增减衣物，注意防晒和保湿。"""
        
        return """🌤️ 天气查询服务

我是专业的天气助手，可以为您提供准确的天气信息。

可查询城市: 北京、上海、广州、深圳、杭州、成都

请告诉我您想查询哪个城市的天气？"""

class DataAnalystAgent(BaseA2AAgent):
    """数据分析智能体 - 专业数据分析和可视化服务"""
    
    agent_id = "data-analyst"
    keywords = ["数据", "分析", "图表", "统计", "可视化", "报表", "data", "analysis", "chart", "statistics"]
    
    def __init__(self):
        super().__init__(
            name="数据分析师",
            description="我是专业的数据分析和可视化智能体，擅长数据处理、统计分析、图表生成和商业洞察"
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一位资深的数据分析师和商业智能专家。

专业技能:
- 数据清洗和预处理
- 统计分析和假设检验
- 数据可视化和图表设计
- 商业洞察和趋势分析
- Python/R数据分析
- SQL数据查询
- 机器学习建模

分析流程:
1. 数据理解和探索
2. 数据质量评估
3. 统计分析执行
4. 可视化图表生成
5. 业务洞察提取
6. 建议和行动方案

回答要求:
1. 提供专业的数据分析思路
2. 推荐合适的分析方法和工具
3. 给出具体的实施步骤
4. 包含代码示例（如果需要）
5. 提供业务解读和建议
6. 用中文详细回答

请为用户提供专业的数据分析服务。"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        return """📊 数据分析服务

我是专业的数据分析师，可以为您提供：

🔍 **数据探索分析**
- 数据质量评估
- 描述性统计分析
- 异常值检测

📈 **统计分析**
- 相关性分析
- 回归分析
- 假设检验

📊 **可视化图表**
- 趋势图、柱状图、散点图
- 热力图、箱线图
- 交互式仪表板

💡 **业务洞察**
- 关键指标解读
- 趋势预测
- 优化建议

请上传您的数据文件或描述具体的分析需求，我将为您提供专业的分析方案。"""

class DocumentWriterAgent(BaseA2AAgent):
    """文档编写智能体 - 专业文档编写和格式化服务"""
    
    agent_id = "document-writer" 
    keywords = ["文档", "报告", "总结", "编写", "格式", "document", "writing", "报表", "方案"]
    
    def __init__(self):
        super().__init__(
            name="文档助手",
            description="我是专业的文档编写和格式化智能体，擅长各类商业文档、技术文档和报告的创作"
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一位资深的技术文档和商业文档写作专家。

专业技能:
- 商业计划书和项目方案
- 技术文档和API文档
- 研究报告和分析报告
- 会议纪要和总结报告
- 用户手册和操作指南
- 学术论文和研究报告

文档类型:
- 项目总结报告
- 技术设计文档
- 商业提案书
- 培训材料
- 流程规范文档
- 用户指南

写作要求:
1. 结构清晰，逻辑严密
2. 语言专业，表达准确
3. 格式规范，排版美观
4. 内容充实，重点突出
5. 符合商业或技术写作标准
6. 用中文撰写

请根据用户需求提供专业的文档编写服务。"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        return """📝 文档编写服务

我是专业的文档助手，可以为您创作各类文档：

📋 **商业文档**
- 项目计划书
- 商业提案
- 工作总结报告
- 会议纪要

📚 **技术文档**
- 系统设计文档
- API文档
- 用户手册
- 技术规范

📊 **分析报告**
- 数据分析报告
- 市场调研报告
- 可行性分析
- 风险评估报告

💼 **管理文档**
- 流程规范
- 培训材料
- 政策文件
- 操作指南

请告诉我您需要什么类型的文档，我将为您提供专业的写作服务。"""

class CodeGeneratorAgent(BaseA2AAgent):
    """代码生成智能体 - 专业编程和代码生成服务"""
    
    agent_id = "code-generator"
    keywords = ["代码", "编程", "脚本", "函数", "算法", "code", "programming", "开发", "软件"]
    
    def __init__(self):
        super().__init__(
            name="代码生成器",
            description="我是专业的编程和代码生成智能体，擅长多种编程语言的代码编写、算法实现和程序优化"
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一位资深的软件工程师和算法专家。

编程技能:
- Python、JavaScript、Java、C++、Go等多种语言
- 数据结构和算法设计
- Web开发（前端/后端）
- 数据库设计和SQL
- API设计和微服务
- 机器学习和AI算法

专业领域:
- 算法实现和优化
- 数据处理和分析脚本
- Web应用开发
- 自动化脚本编写
- 数据库操作
- API集成

代码要求:
1. 代码规范，注释完整
2. 性能优化，考虑边界情况
3. 可读性强，易于维护
4. 包含使用示例和测试
5. 遵循最佳实践
6. 提供详细的技术说明

请根据用户需求提供专业的编程服务。"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        return """💻 代码生成服务

我是专业的代码生成器，可以为您提供：

🐍 **Python开发**
- 数据处理脚本
- Web应用开发
- 机器学习算法
- 自动化工具

🌐 **Web开发**
- 前端界面开发
- 后端API设计
- 数据库操作
- 全栈应用

🔧 **算法实现**
- 排序和搜索算法
- 数据结构实现
- 优化算法
- 数学计算

⚙️ **工具脚本**
- 文件处理工具
- 数据转换脚本
- 系统管理工具
- 批处理脚本

请描述您需要什么功能的代码，我将为您生成高质量的程序。"""

class KnowledgeAgent(BaseA2AAgent):
    """知识问答智能体 - 专业知识查询和解答服务（整合现有知识库）"""
    
    agent_id = "knowledge-agent"
    keywords = ["什么是", "介绍", "解释", "知识", "概念", "what", "explain", "定义", "原理"]
    
    def __init__(self):
        super().__init__(
            name="知识专家",
            description="我是专业的知识问答智能体，拥有广泛的知识库，擅长概念解释、原理分析和知识普及"
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一位博学的知识专家和教育者。

知识领域:
- 科学技术（计算机、物理、化学、生物）
- 人文社科（历史、文学、哲学、心理学）
- 商业管理（经济学、管理学、市场营销）
- 艺术文化（音乐、美术、电影、文学）
- 生活常识（健康、教育、旅游、美食）

专业能力:
- 概念定义和原理解释
- 知识点之间的关联分析
- 复杂概念的简化表达
- 实例举证和类比说明
- 学习建议和延伸阅读

回答标准:
1. 准确性：确保信息的准确性和权威性
2. 全面性：从多个角度全面阐述
3. 易懂性：用通俗易懂的语言解释
4. 逻辑性：保持逻辑清晰的结构
5. 实用性：提供实际应用价值
6. 用中文详细回答

请为用户提供专业的知识解答服务。"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        # 首先尝试在内置知识库中搜索
        try:
            search_result = knowledge_base.search_knowledge(
                user_message, 
                [{"name": "17ba836a79e44dd9a211de926c84b870", "version": 1}]  # knowledge库
            )
            
            if search_result.get("parts") and len(search_result["parts"]) > 0:
                # 格式化知识库结果
                content_parts = []
                for i, part in enumerate(search_result["parts"][:3], 1):  # 取前3个结果
                    content_parts.append(f"""📄 **{i}. {part['docName']}**
{part['content'][:300]}{"..." if len(part['content']) > 300 else ""}
""")
                
                return f"""🧠 知识库查询结果

{chr(10).join(content_parts)}

💡 以上信息来自内置技术知识库。如需更详细信息，可以使用知识库检索接口进一步查询。

TraceId: {search_result.get('traceId', '')}"""
                
        except Exception as e:
            logger.error(f"知识库搜索失败: {str(e)}")
        
        # 回退到默认知识响应
        return """🧠 知识问答服务

我是专业的知识专家，可以为您解答：

🔬 **科学技术**
- 计算机科学和编程
- 人工智能和机器学习
- 物理学和化学原理
- 生物学和医学知识

📚 **人文社科**
- 历史事件和文化
- 文学作品和作家
- 哲学思想和理论
- 心理学和社会学

💼 **商业管理**
- 经济学基础理论
- 企业管理方法
- 市场营销策略
- 投资理财知识

🎨 **艺术文化**
- 音乐和美术鉴赏
- 电影和文学评析
- 传统文化知识
- 现代艺术趋势

请告诉我您想了解什么知识，我将为您提供详细的解答。

💡 提示：我已整合内置知识库，能够为您提供技术文档、产品信息等专业内容。"""

class KnowledgeBase:
    """知识库管理类"""
    
    def __init__(self):
        """初始化知识库"""
        self.knowledge_bases = {}
        self._init_test_data()
        logger.info("知识库初始化完成")
    
    def _init_test_data(self):
        """初始化测试知识库数据"""
        
        # knowledge知识库 - 技术文档和产品信息
        self.knowledge_bases["knowledge"] = {
            "id": "17ba836a79e44dd9a211de926c84b870",
            "name": "技术知识库",
            "version": 1,
            "documents": [
                {
                    "id": "doc_001",
                    "docId": "92debc3c1cd0470bb97c5894678cca20",
                    "docName": "一加手机技术规格.doc",
                    "categoryId": "b605658e9b89434689d5294d83bc89c5",
                    "content": """一加11手机详细技术参数

一、外观与设计
1. 尺寸：高度为200mm，宽度为100mm，厚度为10mm
2. 重量：约为205g
3. 颜色：提供一瞬青和无尽黑两种配色
4. 屏幕：
   - 尺寸：6.7英寸
   - 类型：三星2K+120Hz AMOLED柔性微曲屏
   - 分辨率：3216x1440像素
   - 像素密度：525ppi
   - 屏占比：92.7%
   - 支持LTPO 3.0随动变帧、杜比视界、HDR视频高亮模式等功能

二、性能与配置
1. 处理器：搭载高通第二代骁龙8移动平台，采用台积电4nm工艺
2. CPU：八核处理器，最高主频达到3.2GHz
3. GPU：Adreno 740图形处理器
4. 内存：12GB/16GB LPDDR5X
5. 存储：256GB/512GB UFS 4.0

三、拍照系统
1. 主摄：5000万像素，索尼IMX890传感器
2. 超广角：4800万像素，114°视野
3. 长焦：3200万像素，2倍光学变焦
4. 前置：1600万像素
5. 支持哈苏自然色彩优化""",
                    "html": """<h1>一加11手机详细技术参数</h1>
<h2>一、外观与设计</h2>
<p>1. 尺寸：高度为200mm，宽度为100mm，厚度为10mm</p>
<p>2. 重量：约为205g</p>
<p>3. 颜色：提供一瞬青和无尽黑两种配色</p>
<h3>4. 屏幕：</h3>
<ul>
<li>尺寸：6.7英寸</li>
<li>类型：三星2K+120Hz AMOLED柔性微曲屏</li>
<li>分辨率：3216x1440像素</li>
<li>像素密度：525ppi</li>
<li>屏占比：92.7%</li>
</ul>""",
                    "paths": ["一加手机技术规格.doc"],
                    "fileExtension": "doc",
                    "fileType": "text",
                    "keywords": ["一加11", "手机", "尺寸", "重量", "屏幕", "处理器", "内存", "拍照"]
                },
                {
                    "id": "doc_002", 
                    "docId": "3d9b9d998ba467390ad924adcc4a9cf",
                    "docName": "Python编程指南.pdf",
                    "categoryId": "tech_programming_001",
                    "content": """Python编程语言完整指南

一、Python简介
Python是一种高级编程语言，具有简洁清晰的语法。
创建者：Guido van Rossum
发布时间：1991年

二、基本语法
1. 变量声明：name = "Python"
2. 数据类型：int, float, str, list, dict, tuple
3. 控制结构：if/else, for, while
4. 函数定义：def function_name():

三、高级特性
1. 面向对象编程
2. 装饰器
3. 生成器
4. 上下文管理器
5. 异步编程

四、常用库
1. 数据科学：pandas, numpy, matplotlib
2. Web开发：Django, Flask, FastAPI
3. 机器学习：scikit-learn, tensorflow, pytorch
4. 爬虫：requests, beautifulsoup, scrapy""",
                    "html": """<h1>Python编程语言完整指南</h1>
<h2>一、Python简介</h2>
<p>Python是一种高级编程语言，具有简洁清晰的语法。</p>
<p>创建者：Guido van Rossum</p>
<p>发布时间：1991年</p>""",
                    "paths": ["Python编程指南.pdf"],
                    "fileExtension": "pdf",
                    "fileType": "text",
                    "keywords": ["Python", "编程", "语法", "函数", "变量", "数据类型", "库"]
                },
                {
                    "id": "doc_003",
                    "docId": "ai_tech_spec_001",
                    "docName": "人工智能技术白皮书.docx",
                    "categoryId": "ai_technology_001", 
                    "content": """人工智能技术发展白皮书

一、人工智能概述
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

二、核心技术领域
1. 机器学习（Machine Learning）
   - 监督学习
   - 无监督学习  
   - 强化学习
   
2. 深度学习（Deep Learning）
   - 神经网络
   - 卷积神经网络（CNN）
   - 循环神经网络（RNN）
   - Transformer架构

3. 自然语言处理（NLP）
   - 文本理解
   - 语言生成
   - 机器翻译
   - 对话系统

4. 计算机视觉
   - 图像识别
   - 目标检测
   - 图像分割
   - 视频分析

三、应用场景
1. 智能助手和聊天机器人
2. 自动驾驶技术
3. 医疗诊断
4. 金融风控
5. 智能制造
6. 智慧城市""",
                    "html": """<h1>人工智能技术发展白皮书</h1>
<h2>一、人工智能概述</h2>
<p>人工智能（Artificial Intelligence，AI）是计算机科学的一个分支...</p>
<h2>二、核心技术领域</h2>
<h3>1. 机器学习（Machine Learning）</h3>
<ul><li>监督学习</li><li>无监督学习</li><li>强化学习</li></ul>""",
                    "paths": ["人工智能技术白皮书.docx"],
                    "fileExtension": "docx", 
                    "fileType": "text",
                    "keywords": ["人工智能", "AI", "机器学习", "深度学习", "神经网络", "NLP", "计算机视觉"]
                }
            ]
        }
        
        # attachment知识库 - 附件和多媒体内容
        self.knowledge_bases["attachment"] = {
            "id": "f127a5525dc94879b661f70daada603d",
            "name": "附件知识库", 
            "version": 1,
            "documents": [
                {
                    "id": "att_001",
                    "docId": "img_tech_diagram_001",
                    "docName": "技术架构图.png",
                    "categoryId": "images_tech_001",
                    "content": "这是一张展示微服务技术架构的示意图，包含API网关、服务注册中心、配置中心、负载均衡器等核心组件。",
                    "html": "<p>这是一张展示微服务技术架构的示意图，包含API网关、服务注册中心、配置中心、负载均衡器等核心组件。</p>",
                    "paths": ["技术架构图.png"],
                    "fileExtension": "png",
                    "fileType": "image",
                    "keywords": ["技术架构", "微服务", "API网关", "负载均衡"],
                    "reference": {
                        "img_001": {
                            "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                            "format": "img",
                            "suffix": "png",
                            "link": "https://example.com/images/tech_architecture.png"
                        }
                    }
                },
                {
                    "id": "att_002",
                    "docId": "table_sales_data_001", 
                    "docName": "销售数据统计表.xlsx",
                    "categoryId": "tables_sales_001",
                    "content": "2024年第一季度销售数据统计表，包含各产品线的销售额、增长率、市场份额等关键指标。",
                    "html": "<p>2024年第一季度销售数据统计表，包含各产品线的销售额、增长率、市场份额等关键指标。</p>",
                    "paths": ["销售数据统计表.xlsx"],
                    "fileExtension": "xlsx",
                    "fileType": "table",
                    "keywords": ["销售数据", "统计表", "季度", "增长率", "市场份额"],
                    "reference": {
                        "table_001": {
                            "content": '{"headers":["产品线","销售额(万元)","同比增长率","市场份额"],"rows":[["智能手机",12500,"15.2%","35%"],["平板电脑",3600,"8.7%","12%"],["智能手表",2800,"23.4%","8%"],["耳机配件",1200,"18.9%","5%"]]}',
                            "format": "table", 
                            "suffix": "xlsx",
                            "link": "https://example.com/files/sales_data_q1.xlsx"
                        }
                    }
                },
                {
                    "id": "att_003",
                    "docId": "pdf_manual_001",
                    "docName": "用户操作手册.pdf", 
                    "categoryId": "manuals_user_001",
                    "content": """用户操作手册

第一章：快速入门
1.1 系统要求
- 操作系统：Windows 10/macOS 10.15+/Linux Ubuntu 18.04+
- 内存：4GB RAM（推荐8GB）
- 存储空间：500MB可用空间
- 网络：稳定的互联网连接

1.2 安装步骤
1. 下载安装包
2. 运行安装程序
3. 按照向导完成安装
4. 首次启动并登录

第二章：基本操作
2.1 界面介绍
- 菜单栏：文件、编辑、视图、工具、帮助
- 工具栏：常用功能快捷按钮
- 工作区：主要编辑区域  
- 状态栏：显示当前状态信息

2.2 创建项目
1. 点击"文件"菜单
2. 选择"新建项目"
3. 填写项目信息
4. 选择项目模板
5. 点击"创建"按钮""",
                    "html": """<h1>用户操作手册</h1>
<h2>第一章：快速入门</h2>
<h3>1.1 系统要求</h3>
<ul>
<li>操作系统：Windows 10/macOS 10.15+/Linux Ubuntu 18.04+</li>
<li>内存：4GB RAM（推荐8GB）</li>
<li>存储空间：500MB可用空间</li>
<li>网络：稳定的互联网连接</li>
</ul>""",
                    "paths": ["用户操作手册.pdf"],
                    "fileExtension": "pdf",
                    "fileType": "document",
                    "keywords": ["用户手册", "操作指南", "安装", "系统要求", "快速入门"]
                }
            ]
        }
    
    def search_knowledge(self, query: str, db_list: list) -> dict:
        """
        在指定知识库中搜索相关文档
        
        Args:
            query: 搜索查询字符串
            db_list: 知识库列表
            
        Returns:
            dict: 搜索结果
        """
        try:
            query_lower = query.lower()
            all_results = []
            
            # 遍历每个指定的知识库
            for db_info in db_list:
                db_name = db_info.get('name', '')
                db_version = db_info.get('version', 1)
                
                # 根据知识库ID获取对应的知识库名称
                kb_name = None
                for kb_key, kb_data in self.knowledge_bases.items():
                    if kb_data.get('id') == db_name:
                        kb_name = kb_key
                        break
                
                if not kb_name or kb_name not in self.knowledge_bases:
                    logger.warning(f"知识库 {db_name} 未找到")
                    continue
                
                kb = self.knowledge_bases[kb_name]
                
                # 在该知识库中搜索文档
                for doc in kb['documents']:
                    score = self._calculate_similarity(query_lower, doc)
                    
                    if score > 10:  # 相似度阈值
                        # 分割文档内容为段落列表，按照换行符分割
                        split_content = [line.strip() for line in doc['content'].split('\n') if line.strip()]
                        
                        result = {
                            "id": str(uuid.uuid4()),
                            "title": doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content'],
                            "query": query,
                            "paths": doc['paths'],
                            "splitContent": split_content,
                            "similarQuery": [],
                            "libId": kb['id'],
                            "docId": doc['docId'],
                            "categoryId": doc['categoryId'],
                            "docName": doc['docName'],
                            "content": doc['content'],
                            "html": doc['html'],
                            "fileExtension": doc['fileExtension'],
                            "score": score,
                            "fileType": doc['fileType'],
                            "type": "Es",
                            "sort": len(all_results) + 1,
                            "reference": doc.get('reference', {})
                        }
                        all_results.append(result)
            
            # 按相似度分数排序
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            # 生成TraceId
            trace_id = str(uuid.uuid4()).replace('-', '')
            
            return {
                "parts": all_results[:10],  # 最多返回10个结果
                "query": query,
                "querykeywords": self._extract_keywords(query),
                "traceId": trace_id
            }
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {str(e)}")
            return {
                "parts": [],
                "query": query,
                "querykeywords": [],
                "traceId": str(uuid.uuid4()).replace('-', '')
            }
    
    def _calculate_similarity(self, query: str, document: dict) -> float:
        """
        计算查询与文档的相似度分数
        
        Args:
            query: 查询字符串
            document: 文档对象
            
        Returns:
            float: 相似度分数
        """
        try:
            content_lower = document['content'].lower()
            doc_name_lower = document['docName'].lower()
            keywords = document.get('keywords', [])
            
            score = 0.0
            
            # 关键词完全匹配（高分）
            for keyword in keywords:
                if keyword.lower() in query:
                    score += 25.0
            
            # 文档名匹配
            query_words = query.split()
            for word in query_words:
                if word in doc_name_lower:
                    score += 15.0
            
            # 内容匹配
            for word in query_words:
                if word in content_lower:
                    score += 8.0
                    
            # 部分匹配
            for word in query_words:
                for keyword in keywords:
                    if word in keyword.lower() or keyword.lower() in word:
                        score += 5.0
            
            return round(score, 6)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {str(e)}")
            return 0.0
    
    def _extract_keywords(self, query: str) -> list:
        """
        从查询中提取关键词
        
        Args:
            query: 查询字符串
            
        Returns:
            list: 关键词列表
        """
        try:
            # 简单的关键词提取（可以集成更复杂的NLP库）
            import re
            
            # 去除标点符号，分词
            words = re.findall(r'\b\w+\b', query.lower())
            
            # 过滤停用词
            stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '我们', '你们', '他们', 
                         'and', 'or', 'but', 'the', 'a', 'an', 'to', 'for', 'of', 'with', 'by'}
            
            keywords = [word for word in words if word not in stop_words and len(word) > 1]
            
            return keywords[:10]  # 最多返回10个关键词
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []

# 创建全局知识库实例
knowledge_base = KnowledgeBase()

# 创建全局工具注册表实例
tool_registry = MCPToolRegistry()

# 创建A2A智能体映射表
AGENT_MAPPING = {
    "weather-agent": WeatherAgent(),
    "data-analyst": DataAnalystAgent(),
    "document-writer": DocumentWriterAgent(),
    "code-generator": CodeGeneratorAgent(),
    "knowledge-agent": KnowledgeAgent()
}

def get_agent_by_id(agent_id: str) -> Optional[BaseA2AAgent]:
    """
    根据智能体ID获取智能体实例
    
    Args:
        agent_id: 智能体标识符
        
    Returns:
        Optional[BaseA2AAgent]: 智能体实例，如果未找到返回None
    """
    agent = AGENT_MAPPING.get(agent_id)
    if agent:
        logger.info(f"📍 路由到智能体: {agent.name} (ID: {agent_id})")
    else:
        logger.warning(f"⚠️ 未找到智能体: {agent_id}")
    return agent

def route_to_agent(agent_id: str = None, message: str = "") -> str:
    """
    智能体路由逻辑
    
    Args:
        agent_id: 指定的智能体ID（优先使用）
        message: 用户消息内容（用于关键词匹配）
        
    Returns:
        str: 路由到的智能体ID
    """
    # 1. 优先使用指定的agentId
    if agent_id and agent_id in AGENT_MAPPING:
        logger.info(f"🎯 使用指定智能体: {agent_id}")
        return agent_id
    
    # 2. 基于消息内容的关键词匹配
    if message:
        message_lower = message.lower()
        
        # 计算每个智能体的匹配分数
        agent_scores = {}
        for aid, agent in AGENT_MAPPING.items():
            score = 0
            for keyword in agent.keywords:
                if keyword.lower() in message_lower:
                    score += 1
            agent_scores[aid] = score
        
        # 找到得分最高的智能体
        if agent_scores:
            best_agent = max(agent_scores, key=agent_scores.get)
            if agent_scores[best_agent] > 0:
                logger.info(f"🎯 基于关键词匹配路由到: {best_agent} (得分: {agent_scores[best_agent]})")
                return best_agent
    
    # 3. 默认使用知识问答智能体
    logger.info("🎯 使用默认智能体: knowledge-agent")
    return "knowledge-agent"

def log_agent_environment_info():
    """记录A2A智能体环境信息"""
    logger.info("🌐 A2A智能体环境配置:")
    logger.info(f"   LangChain可用: {'是' if LLM_AVAILABLE else '否'}")
    if LLM_AVAILABLE:
        logger.info(f"   OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'Not set')}")
        logger.info(f"   BASE_LLM: {os.getenv('BASE_LLM', 'Not set')}")
        logger.info(f"   OPENAI_API_KEY: {'设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
    
    logger.info("🤖 可用A2A智能体列表:")
    for agent_id, agent in AGENT_MAPPING.items():
        logger.info(f"   • {agent_id}: {agent.name}")
        logger.info(f"     关键词: {', '.join(agent.keywords[:5])}{'...' if len(agent.keywords) > 5 else ''}")
        logger.info(f"     LLM支持: {'是' if agent.llm_client else '否'}")

def generate_sse_stream(agent_id: str, session_id: str, task_id: str, messages: List[Dict], user_id: str = "default_user") -> str:
    """
    Flask SSE流生成器
    
    Args:
        agent_id: 智能体ID
        session_id: 会话ID
        task_id: 任务ID
        messages: 消息列表
        user_id: 用户ID
        
    Yields:
        str: SSE格式的数据流
    """
    try:
        # 首先检查传入的agent_id是否存在
        if agent_id and agent_id not in AGENT_MAPPING:
            error_response = {
                "sessionId": session_id,
                "taskId": task_id,
                "type": "text",
                "content": f"❌ 智能体 '{agent_id}' 不存在。可用智能体: {', '.join(AGENT_MAPPING.keys())}",
                "final": True,
                "status": False,
                "errorMsg": f"Agent '{agent_id}' not found"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
            return
        
        # 路由到合适的智能体
        final_agent_id = route_to_agent(agent_id, "")
        agent = get_agent_by_id(final_agent_id)
        
        if not agent:
            error_response = {
                "sessionId": session_id,
                "taskId": task_id,
                "type": "text",
                "content": f"❌ 智能体路由失败。可用智能体: {', '.join(AGENT_MAPPING.keys())}",
                "final": True,
                "status": False,
                "errorMsg": f"Agent routing failed"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
            return
        
        # 初始化会话
        if session_id not in sessions:
            sessions[session_id] = {
                "agent_id": final_agent_id,
                "task_id": task_id,
                "history": [],
                "agent_name": agent.name
            }
            logger.info(f"📝 创建新会话: {session_id}")
        
        session = sessions[session_id]
        
        # 处理消息
        for message in messages:
            msg_type = message.get("type")
            content = message.get("content")
            
            logger.info(f"📨 处理消息类型: {msg_type}")
            
            if msg_type == "text" and content:
                # 记录用户消息
                session["history"].append({"role": "user", "content": content})
                
                # 发送技能开始事件
                skill_start_data = {
                    "sessionId": session_id,
                    "taskId": task_id,
                    "type": "skill_start",
                    "content": {
                        "icon": "🤖",
                        "name": f"{agent.name}处理工具",
                        "skillInput": json.dumps({"query": content}, ensure_ascii=False)
                    },
                    "final": False,
                    "status": True
                }
                yield f"data: {json.dumps(skill_start_data, ensure_ascii=False)}\n\n"
                
                # 调用智能体处理消息
                logger.info(f"🎯 {agent.name} 开始处理用户消息...")
                result = agent.process_message(content)
                
                # 发送技能结束事件
                skill_end_data = {
                    "sessionId": session_id,
                    "taskId": task_id,
                    "type": "skill_end",
                    "content": {
                        "name": f"{agent.name}处理工具",
                        "skillOutput": json.dumps({
                            "output": {
                                "content": result["response"],
                                "agent_info": {
                                    "name": result["agent_name"],
                                    "id": result["agent_id"],
                                    "llm_used": result["llm_used"]
                                }
                            }
                        }, ensure_ascii=False)
                    },
                    "final": False,
                    "status": True
                }
                yield f"data: {json.dumps(skill_end_data, ensure_ascii=False)}\n\n"
                
                # 发送最终响应
                final_response_data = {
                    "sessionId": session_id,
                    "taskId": task_id,
                    "type": "text",
                    "content": result["response"],
                    "final": True,
                    "status": True,
                    "agent_info": {
                        "name": result["agent_name"],
                        "id": result["agent_id"],
                        "llm_used": result["llm_used"]
                    }
                }
                
                yield f"data: {json.dumps(final_response_data, ensure_ascii=False)}\n\n"
                session["history"].append({"role": "assistant", "content": result["response"]})
                
                logger.info(f"✅ {agent.name} 消息处理完成")
                
    except Exception as e:
        logger.error(f"❌ SSE响应生成异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_data = {
            "sessionId": session_id,
            "taskId": task_id,
            "type": "text",
            "content": f"❌ 处理过程中发生错误: {str(e)}",
            "final": True,
            "status": False,
            "errorMsg": str(e)
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

@app.route('/agentV2/multi-agents/mcp/api/tool/callTool', methods=['POST'])
def call_tool():
    """
    MCP工具调用接口
    
    实现标准的MCP工具调用协议，根据toolId路由到相应的工具处理函数。
    """
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        # 记录请求日志
        logger.info(f"收到MCP工具调用请求: {json.dumps(request_data, ensure_ascii=False)}")
        
        if not request_data:
            return json_response({
                "type": "error",
                "content": "",
                "status": False,
                "errorMsg": "请求体为空，请提供有效的JSON数据包含toolId和arguments字段"
            }, 400)
        
        # 提取参数
        tool_id = request_data.get('toolId', '')
        arguments = request_data.get('arguments', {})
        
        if not tool_id:
            return json_response({
                "type": "error",
                "content": "",
                "status": False,
                "errorMsg": "缺少必需的toolId参数，请提供有效的工具ID"
            }, 400)
        
        # 获取工具处理函数
        tool_handler = tool_registry.get_tool(tool_id)
        
        if not tool_handler:
            return json_response({
                "type": "error",
                "content": "",
                "status": False,
                "errorMsg": f"工具 '{tool_id}' 未找到。可用工具: {', '.join(tool_registry.list_tools().keys())}"
            }, 404)
        
        # 执行工具
        logger.info(f"执行工具: {tool_id}")
        result = tool_handler(arguments)
        
        # 记录响应日志
        logger.info(f"工具执行完成: {tool_id}, 状态: {'成功' if result.status else '失败'}")
        
        return json_response(result.to_dict())
        
    except Exception as e:
        logger.error(f"MCP工具调用发生异常: {str(e)}", exc_info=True)
        return json_response({
            "type": "error",
            "content": "",
            "status": False,
            "errorMsg": f"服务器内部错误: {str(e)}"
        }, 500)

@app.route('/agentV2/multi-agents/mcp/api/tool/list', methods=['GET'])
def list_tools():
    """
    获取所有可用工具列表
    
    返回当前注册的所有工具及其描述信息。
    """
    try:
        tools_info = tool_registry.list_tools()
        
        return json_response({
            "type": "list",
            "content": f"共找到 {len(tools_info)} 个可用工具",
            "status": True,
            "tools": tools_info
        })
        
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}")
        return json_response({
            "type": "error",
            "content": "",
            "status": False,
            "errorMsg": f"获取工具列表失败: {str(e)}"
        }, 500)

@app.route('/mae/api/v1.0/rest/a2aChat', methods=['POST'])
def a2a_chat():
    """
    A2A调用执行接口
    
    实现标准的A2A调用协议，支持多智能体路由和SSE流式响应。
    """
    try:
        request_data = request.get_json()
        
        agent_id = request_data.get("agentId")
        session_id = request_data.get("sessionId", str(uuid.uuid4()))
        user_id = request_data.get("userId", "default_user")
        messages = request_data.get("messages", [])
        
        logger.info(f"📞 收到A2A调用请求:")
        logger.info(f"   Agent ID: {agent_id}")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Messages: {len(messages)} 条")
        
        if not agent_id:
            logger.error("❌ agentId 参数缺失")
            return json_response({
                "error": "agentId is required",
                "status": False,
                "errorMsg": "agentId参数是必需的"
            }, 400)
        
        # 检查智能体是否存在
        if agent_id not in AGENT_MAPPING:
            logger.error(f"❌ 智能体 '{agent_id}' 不存在")
            return json_response({
                "error": f"Agent '{agent_id}' not found",
                "status": False,
                "errorMsg": f"智能体 '{agent_id}' 不存在。可用智能体: {', '.join(AGENT_MAPPING.keys())}",
                "available_agents": list(AGENT_MAPPING.keys())
            }, 404)
        
        if not messages:
            logger.error("❌ messages 参数缺失")
            return json_response({
                "error": "messages is required", 
                "status": False,
                "errorMsg": "messages参数是必需的"
            }, 400)
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"🎯 开始处理A2A任务: {task_id}")
        
        # 返回SSE流
        return Response(
            generate_sse_stream(agent_id, session_id, task_id, messages, user_id),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ A2A调用处理异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response = {
            "sessionId": session_id if 'session_id' in locals() else "",
            "taskId": task_id if 'task_id' in locals() else "",
            "type": "text",
            "content": f"❌ 服务错误：{str(e)}",
            "final": True,
            "status": False,
            "errorMsg": str(e)
        }
        return json_response(error_response, 500)

@app.route('/agentV2/multi-agents/mcp/knowledge/retrieval', methods=['POST'])
def knowledge_retrieval():
    """
    知识库检索接口
    
    实现标准的MCP知识库检索协议，根据查询内容在指定知识库中搜索相关文档。
    """
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        # 记录请求日志
        logger.info(f"收到知识库检索请求: {json.dumps(request_data, ensure_ascii=False)}")
        
        if not request_data:
            return json_response({
                "retcode": 400,
                "desc": "请求体为空",
                "errorInfo": "请求体为空，请提供有效的JSON数据包含content和dbList字段",
                "data": None
            }, 400)
        
        # 提取参数
        content = request_data.get('content', '')
        db_list = request_data.get('dbList', [])
        
        if not content:
            return json_response({
                "retcode": 400,
                "desc": "缺少必需的content参数",
                "errorInfo": "content参数不能为空",
                "data": None
            }, 400)
        
        if not db_list:
            return json_response({
                "retcode": 400,
                "desc": "缺少必需的dbList参数", 
                "errorInfo": "dbList参数不能为空",
                "data": None
            }, 400)
        
        # 执行知识库搜索
        logger.info(f"在知识库中搜索: {content}")
        search_result = knowledge_base.search_knowledge(content, db_list)
        
        # 记录响应日志
        logger.info(f"知识库搜索完成，返回 {len(search_result.get('parts', []))} 个结果")
        
        # 返回标准格式的响应
        response = {
            "retcode": 200,
            "desc": "成功",
            "errorInfo": "",
            "data": search_result
        }
        
        return json_response(response)
        
    except Exception as e:
        logger.error(f"知识库检索发生异常: {str(e)}", exc_info=True)
        return json_response({
            "retcode": 500,
            "desc": "服务器内部错误",
            "errorInfo": f"知识库检索失败: {str(e)}",
            "data": None
        }, 500)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return json_response({
        "status": "healthy",
        "server": "MCP Normal Test Server",
        "version": "1.1.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "tools_count": len(tool_registry.list_tools()),
        "knowledge_bases": ["knowledge", "attachment"]
    })

@app.route('/', methods=['GET'])
def index():
    """根路径接口，提供服务器信息"""
    tools_info = tool_registry.list_tools()
    
    return json_response({
        "message": "MCP Normal Test Server",
        "description": "标准MCP工具调用和知识库检索测试服务器",
        "version": "1.1.0",
        "port": SERVER_PORT,
        "endpoints": {
            "tool_call": "/agentV2/multi-agents/mcp/api/tool/callTool",
            "tool_list": "/agentV2/multi-agents/mcp/api/tool/list",
            "knowledge_retrieval": "/agentV2/multi-agents/mcp/knowledge/retrieval",
            "health": "/health"
        },
        "available_tools": list(tools_info.keys()),
        "tools_detail": tools_info,
        "knowledge_bases": {
            "knowledge": {
                "id": "17ba836a79e44dd9a211de926c84b870",
                "name": "技术知识库",
                "documents": 3
            },
            "attachment": {
                "id": "f127a5525dc94879b661f70daada603d", 
                "name": "附件知识库",
                "documents": 3
            }
        }
    })

def print_startup_info():
    """打印统一服务器启动信息"""
    tools_info = tool_registry.list_tools()
    
    print("=" * 100)
    print("🚀 MCP + A2A 统一测试服务器启动成功！")
    print("=" * 100)
    print(f"🌐 服务器地址: http://{SERVER_HOST}:{SERVER_PORT}")
    print()
    print("📡 MCP接口:")
    print(f"   🔧 工具调用: http://{SERVER_HOST}:{SERVER_PORT}/agentV2/multi-agents/mcp/api/tool/callTool")
    print(f"   📋 工具列表: http://{SERVER_HOST}:{SERVER_PORT}/agentV2/multi-agents/mcp/api/tool/list") 
    print(f"   🔍 知识检索: http://{SERVER_HOST}:{SERVER_PORT}/agentV2/multi-agents/mcp/knowledge/retrieval")
    print()
    print("📡 A2A接口:")
    print(f"   🤖 智能体调用: http://{SERVER_HOST}:{SERVER_PORT}/mae/api/v1.0/rest/a2aChat")
    print(f"   📱 智能体列表: http://{SERVER_HOST}:{SERVER_PORT}/agents")
    print(f"   ℹ️ 智能体详情: http://{SERVER_HOST}:{SERVER_PORT}/agents/<agent_id>")
    print()
    print("📡 系统接口:")
    print(f"   💚 健康检查: http://{SERVER_HOST}:{SERVER_PORT}/health")
    print(f"   ℹ️ 服务信息: http://{SERVER_HOST}:{SERVER_PORT}/")
    print()
    print(f"🔧 MCP工具 ({len(tools_info)} 个):")
    for tool_id, tool_info in tools_info.items():
        print(f"   📦 {tool_id}: {tool_info['description'][:50]}{'...' if len(tool_info['description']) > 50 else ''}")
    print()
    print(f"🤖 A2A智能体 ({len(AGENT_MAPPING)} 个):")
    for agent_id, agent in AGENT_MAPPING.items():
        llm_status = "✅ LLM" if agent.llm_client else "🔄 本地"
        print(f"   🎯 {agent_id}: {agent.name} ({llm_status})")
        print(f"      关键词: {', '.join(agent.keywords[:3])}{'...' if len(agent.keywords) > 3 else ''}")
    print()
    print("📚 知识库信息:")
    print(f"   📖 knowledge (技术文档): 3个文档")
    print(f"   📎 attachment (附件资源): 3个文档")
    print()
    print("🌐 环境信息:")
    print(f"   LangChain支持: {'✅ 可用' if LLM_AVAILABLE else '❌ 不可用'}")
    if LLM_AVAILABLE:
        print(f"   OpenAI配置: {'✅ 已配置' if os.getenv('OPENAI_API_KEY') else '❌ 未配置'}")
        print(f"   模型: {os.getenv('BASE_LLM', 'openai/gpt-oss-20b')}")
    print()
    print("📝 测试示例:")
    print("   # MCP工具调用:")
    print("   curl -X POST http://localhost:18585/agentV2/multi-agents/mcp/api/tool/callTool \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"toolId\": \"calculator\", \"arguments\": {\"expression\": \"1+1\"}}'")
    print()
    print("   # MCP知识库检索:")
    print("   curl -X POST http://localhost:18585/agentV2/multi-agents/mcp/knowledge/retrieval \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"content\": \"一加11手机\", \"dbList\": [{\"name\": \"17ba836a79e44dd9a211de926c84b870\"}]}'")
    print()
    print("   # A2A智能体调用:")
    print("   curl -X POST http://localhost:18585/mae/api/v1.0/rest/a2aChat \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"agentId\": \"weather-agent\", \"sessionId\": \"test\", \"userId\": \"test_user\", \"messages\": [{\"type\": \"text\", \"content\": \"北京天气\"}]}'")
    print()
    print("   # 获取智能体列表:")
    print("   curl http://localhost:18585/agents")
    print()
    print("🛑 按 Ctrl+C 停止服务器")
    print("=" * 100)

@app.route('/agents', methods=['GET'])
def list_agents():
    """获取所有可用A2A智能体列表"""
    try:
        agents_info = []
        
        for agent_id, agent in AGENT_MAPPING.items():
            agent_info = {
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
                "keywords": agent.keywords,
                "llm_enabled": agent.llm_client is not None,
                "status": "active"
            }
            agents_info.append(agent_info)
        
        return json_response({
            "type": "list",
            "content": f"共找到 {len(agents_info)} 个可用智能体",
            "status": True,
            "agents": agents_info,
            "total": len(agents_info),
            "llm_available": LLM_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"获取智能体列表失败: {str(e)}")
        return json_response({
            "type": "error",
            "content": "",
            "status": False,
            "errorMsg": f"获取智能体列表失败: {str(e)}"
        }, 500)

@app.route('/agents/<agent_id>', methods=['GET'])
def get_agent_info(agent_id: str):
    """获取特定智能体详细信息"""
    try:
        agent = AGENT_MAPPING.get(agent_id)
        
        if not agent:
            return json_response({
                "type": "error",
                "content": "",
                "status": False,
                "errorMsg": f"智能体 '{agent_id}' 未找到。可用智能体: {', '.join(AGENT_MAPPING.keys())}"
            }, 404)
        
        agent_detail = {
            "id": agent_id,
            "name": agent.name,
            "description": agent.description,
            "keywords": agent.keywords,
            "llm_enabled": agent.llm_client is not None,
            "llm_model": os.getenv('BASE_LLM', 'openai/gpt-oss-20b') if agent.llm_client else None,
            "system_prompt_preview": agent._get_system_prompt()[:200] + "..." if len(agent._get_system_prompt()) > 200 else agent._get_system_prompt(),
            "status": "active",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        return json_response({
            "type": "detail",
            "content": f"智能体 {agent.name} 详细信息",
            "status": True,
            "agent": agent_detail
        })
        
    except Exception as e:
        logger.error(f"获取智能体信息失败: {str(e)}")
        return json_response({
            "type": "error",
            "content": "",
            "status": False,
            "errorMsg": f"获取智能体信息失败: {str(e)}"
        }, 500)

if __name__ == '__main__':
    # 记录A2A智能体环境信息
    log_agent_environment_info()
    print_startup_info()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True) 