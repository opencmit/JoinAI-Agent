import requests
import json
import aiohttp
import asyncio

import uuid
from copilotkit.langgraph import copilotkit_emit_tool_call, copilotkit_customize_config
from langchain_core.runnables import RunnableConfig
from typing import Tuple, Union
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, ToolCall  # 添加消息类型导入
from langchain_openai import ChatOpenAI  # 添加OpenAI客户端导入
from langgraph_agent.graph.state import AgentState
from typing import Optional, Any, Callable, List, Dict
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv
import os
import re

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def sanitize_string_for_json(text: str) -> str:
    """
    增强版字符清理函数，更好地处理JSON格式错误
    """
    if not isinstance(text, str):
        return str(text)

    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)

    # 正确处理转义字符的顺序很重要
    text = text.replace('\\', '\\\\')  # 先处理反斜杠
    text = text.replace('"', '\\"')  # 正确转义双引号，而不是替换
    text = text.replace('\n', '\\n')  # 保持换行符的JSON格式
    text = text.replace('\r', '\\r')  # 保持回车符的JSON格式
    text = text.replace('\t', '\\t')  # 保持制表符的JSON格式

    # 处理其他可能有问题的字符
    text = text.replace('\b', '\\b')  # 退格符
    text = text.replace('\f', '\\f')  # 换页符

    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def safe_json_dumps(data: any, **kwargs) -> str:
    """
    安全的JSON序列化函数，处理可能的格式错误
    """
    try:
        # 首先尝试标准序列化
        return json.dumps(data, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"JSON序列化失败，尝试清理数据: {str(e)}")
        # 如果失败，递归清理数据
        cleaned_data = deep_clean_for_json(data)
        try:
            return json.dumps(cleaned_data, ensure_ascii=False, **kwargs)
        except Exception as clean_e:
            logger.error(f"清理后JSON序列化仍然失败: {str(clean_e)}")
            # 最后的降级方案：强制转换为字符串
            return json.dumps(str(data), ensure_ascii=False, **kwargs)


def deep_clean_for_json(obj):
    """
    递归清理对象以确保JSON序列化兼容性
    """
    if isinstance(obj, str):
        return sanitize_string_for_json(obj)
    elif isinstance(obj, dict):
        cleaned_dict = {}
        for k, v in obj.items():
            # 清理键名
            clean_key = sanitize_string_for_json(str(k)) if not isinstance(k, (int, float)) else k
            cleaned_dict[clean_key] = deep_clean_for_json(v)
        return cleaned_dict
    elif isinstance(obj, list):
        return [deep_clean_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return [deep_clean_for_json(item) for item in obj]
    elif isinstance(obj, (int, float, bool, type(None))):
        return obj
    else:
        # 对于其他类型，转换为字符串并清理
        return sanitize_string_for_json(str(obj))


async def async_http_post(url: str, json_payload: str, headers: Dict[str, str], timeout: int = 300) -> Dict[str, Any]:
    """
    异步HTTP POST请求函数
    """
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        async with session.post(
            url,
            data=json_payload.encode('utf-8'),
            headers=headers
        ) as response:
            response_text = await response.text()
            
            return {
                'status_code': response.status,
                'headers': dict(response.headers),
                'text': response_text
            }


def debug_json_error(data, context=""):
    """
    调试JSON格式错误的工具函数
    """
    print(f"\n=== JSON调试 - {context} ===")
    try:
        # 尝试序列化
        json_str = safe_json_dumps(data, indent=2)
        print("✅ JSON格式正确")
        return json_str
    except Exception as e:
        print(f"❌ JSON格式错误: {str(e)}")

        # 递归检查每个字段
        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    json.dumps({key: value}, ensure_ascii=False)
                except Exception as field_e:
                    print(f"  问题字段: {key} = {repr(value)[:200]}")
                    print(f"  错误: {str(field_e)}")

        return None


@dataclass
class MCPToolInfo:
    """MCP工具信息数据类 - 增加新字段"""
    tool_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    type: str = "normal"  # "normal", "knowledge", or "attachment"
    arguments: List[Dict[str, Any]] = None  # 前端传递的参数
    mcp_server_url: str = None  # 新增：MCP服务器URL
    user_id: str = None  # 新增：用户ID


class MCPToolExecutionResult:
    """MCP工具执行结果类"""

    def __init__(self, type: str, content: str, status: bool, error_msg: str = ""):
        self.type = type
        self.content = content
        self.status = status
        self.error_msg = error_msg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "status": self.status,
            "error_msg": self.error_msg
        }


def create_default_llm_client():
    """
    根据环境变量创建默认的LLM客户端

    Returns:
        ChatOpenAI: 配置好的LLM客户端
    """
    try:
        # 从环境变量获取配置
        api_key = os.getenv('OPENAI_API_KEY', 'sk-e0913a950ebc4709879548874c8e10ef')
        base_url = os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        model_name = os.getenv('BASE_LLM', 'qwen2.5-32b-instruct')

        logger.info(f"创建默认LLM客户端 - 模型: {model_name}, 基础URL: {base_url}")

        # 创建ChatOpenAI客户端
        llm_client = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=0.1,  # 设置较低的温度以获得更确定的结果
            max_tokens=2048,  # 设置最大token数
            timeout=30,  # 设置超时时间
        )

        logger.info("默认LLM客户端创建成功")
        return llm_client

    except Exception as e:
        logger.error(f"创建默认LLM客户端失败: {str(e)}")
        logger.warning("将使用无LLM模式运行")
        return None


def extract_user_query_from_state(state: Dict[str, Any]) -> str:
    """
    从状态中提取用户的最新查询

    Args:
        state: Agent状态

    Returns:
        str: 用户的查询内容
    """
    if not isinstance(state, dict) or 'messages' not in state:
        return ""

    # 从消息历史中逆序查找用户的最新消息
    for message in reversed(state.get('messages', [])):
        if hasattr(message, 'type') and message.type == "human":
            return message.content
        elif isinstance(message, dict) and message.get('type') == 'human':
            return message.get('content', '')

    return ""

async def summarize_result_with_llm(llm_client: ChatOpenAI, result: MCPToolExecutionResult, tool_name: str) -> str:
    """
    使用大模型对执行结果进行总结 - 优化版本

    Args:
        result: MCP工具执行结果
        tool_name: 工具名称

    Returns:
        str: 总结后的结果
    """
    # 如果结果内容太短，不需要总结
    if len(result.content) < 200:
        return result.content

    try:
        if not result.status:
            summary_prompt = f"""
            工具 "{tool_name}" 执行失败。
            错误信息: {result.error_msg}
            请对此错误进行简洁的总结和分析。
            """
        else:
            # 清理内容用于prompt
            clean_content = sanitize_string_for_json(result.content[:2000])  # 限制长度避免超出上下文

            summary_prompt = f"""
            工具 "{tool_name}" 执行成功，返回结果如下：
            {clean_content}

            请对以上结果进行简洁明了的总结，突出关键信息。
            保持总结在200字以内。
            """

        # 创建正确的消息格式
        messages = [HumanMessage(content=summary_prompt)]

        # 调用大模型进行总结
        # 此处大模型的总结不需要emit消息，最后会有一个整体的消息emit
        modified_config = copilotkit_customize_config(
            emit_messages=False,  # if you want to disable message streaming #
            emit_tool_calls=False  # if you want to disable tool call streaming #
        )
        response = await llm_client.ainvoke(messages, modified_config)

        # 正确处理响应
        if hasattr(response, 'content'):
            summarized = response.content
        else:
            # 如果response是字符串，直接返回
            summarized = str(response)

        # 清理总结结果
        summarized = sanitize_string_for_json(summarized)

        # 如果总结结果比原始内容还长，返回原始内容
        if len(summarized) > len(result.content):
            return result.content

        return summarized

    except Exception as e:
        logger.error(f"大模型总结失败: {str(e)}")
        # 返回原始结果而不是错误信息
        return result.content

class LangGraphMCPTool(BaseTool):
    """转换后的LangGraph工具类 - 修复版本，增加新字段"""

    # 基类必需的字段
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")

    # 自定义字段
    tool_id: str = Field(description="MCP工具的唯一标识符")
    tool_type: str = Field(default="normal", description="工具类型: normal, knowledge, attachment")
    predefined_arguments: Dict[str, Any] = Field(default_factory=dict, description="预定义参数列表")
    llm_client: Optional[Any] = Field(default=None, description="LLM客户端用于参数提取")
    mcp_server_url: Optional[str] = Field(default=None, description="MCP服务器URL")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    
    normal_tool_url: Optional[str] = Field(default=None, description="普通工具的API URL")
    knowledge_tool_url: Optional[str] = Field(default=None, description="知识库工具的API URL (同时用于attachment工具)")

    class Config:
        # 允许任意类型的字段（用于Callable等复杂类型）
        arbitrary_types_allowed = True

    def __init__(self, mcp_tool_info: MCPToolInfo, llm_client: Optional[Any] = None, **kwargs):
        # 清理工具名称和描述中的特殊字符
        safe_name = sanitize_string_for_json(mcp_tool_info.name)
        safe_description = sanitize_string_for_json(mcp_tool_info.description)

        # 创建动态参数模式
        args_schema = self._create_args_schema(mcp_tool_info)

        # 准备所有字段的数据（包括基类和自定义字段）
        all_fields = {
            # 基类必需的字段
            'name': safe_name,
            'description': safe_description,
            'args_schema': args_schema,

            # 自定义字段
            'tool_id': mcp_tool_info.tool_id,
            'tool_type': mcp_tool_info.type,
            'predefined_arguments': mcp_tool_info.arguments or {},
            'llm_client': llm_client,
            'mcp_server_url': mcp_tool_info.mcp_server_url,
            'user_id': mcp_tool_info.user_id,

            'normal_tool_url': f"{os.environ.get('MCP_BASE_URL', 'http://localhost:5000')}/agentV2/multi-agents/mcp/api/tool/callTool",
            'knowledge_tool_url': f"{os.environ.get('MCP_BASE_URL', 'http://localhost:5000')}/agentV2/multi-agents/mcp/knowledge/retrieval",

            # 其他可能的参数
            **kwargs
        }

        # 调用父类构造函数，传递所有字段
        super().__init__(**all_fields)

        # 保存原始参数定义以供LLM参数提取使用
        self._original_parameters = mcp_tool_info.parameters

        # 增强调试信息：打印工具初始化信息
        print(f"\n======== 初始化 MCP 工具 ========")
        print(f"工具名称: {safe_name}")
        print(f"工具ID: {mcp_tool_info.tool_id}")
        print(f"工具类型: {mcp_tool_info.type}")
        print(f"工具描述: {safe_description}")
        print(f"MCP服务器URL: {self.mcp_server_url}")
        print(f"用户ID: {self.user_id}")
        print(f"支持LLM参数提取: {llm_client is not None}")
        if mcp_tool_info.arguments:
            try:
                args_str = safe_json_dumps(mcp_tool_info.arguments)
                print(f"预定义参数: {args_str[:300]}...")
            except Exception as e:
                print(f"预定义参数格式错误: {str(e)}")
        print("================================\n")

    def _create_args_schema(self, mcp_tool_info: MCPToolInfo) -> type[BaseModel]:
        """根据MCP工具参数创建Pydantic模式 - 增强版"""
        from pydantic import BaseModel, Field

        # 创建字段注解字典
        annotations = {}
        field_definitions = {}

        # 对于知识库和附件类型的工具，只需要content参数
        if mcp_tool_info.type in ["knowledge", "attachment"]:
            annotations['content'] = str
            field_definitions['content'] = Field(description=sanitize_string_for_json("用户查询内容"))
        else:
            # 对于普通工具，使用query参数并提供详细描述
            tool_specific_desc = {
                "supplychain_data_analysis": "用户的供应链相关查询，如'帮我查询一采集中度排名前10的省公司'",
                "query_wb_goods": "省公司商品查询请求，包含手机号和业务类型信息",
                "product-recommend": "5G产品推荐查询，包含手机号和产品类型",
                "query-commodity-info": "商品信息查询请求，可能包含省份、产品ID或联系人信息",
                "opr_sms": "短信相关操作请求，如申请短信模板"
            }

            desc = tool_specific_desc.get(mcp_tool_info.tool_id,
                                          "用户的查询内容，工具将从中自动提取所需参数")

            annotations['query'] = str
            field_definitions['query'] = Field(description=sanitize_string_for_json(desc))

        # 动态创建Pydantic模型
        class_dict = {
            '__annotations__': annotations,
            **field_definitions
        }

        ArgsSchema = type(f"{sanitize_string_for_json(mcp_tool_info.name)}Args", (BaseModel,), class_dict)
        return ArgsSchema

    def _get_tool_specific_extraction_hints(self, tool_id: str, tool_parameters: Dict[str, Any]) -> str:
        """
        为特定工具提供参数提取提示
        """
        tool_hints = {
            "supplychain_data_analysis": """
            特殊说明：
            - query参数应该是用户的完整查询内容
            - 直接传递用户的原始问题即可
            - 示例：
            * 用户说"帮我查询一采集中度排名前10的省公司" → query: "帮我查询一采集中度排名前10的省公司"
            * 用户说"查询北京一采执行金额同比/环比情况" → query: "查询北京一采执行金额同比/环比情况"
            """,

            "query_wb_goods": """
            特殊说明：
            - serviceNumber和xsgRouteValue通常是同一个手机号
            - busiType映射：宽带=1, 号卡=2, 组合包=3, 融合=4, 家庭圈=5
            - queryType：精确查询=1（需要goodsId）, 省公司自主查询=2
            - 默认值：xsgRouteType="01", serviceType="01", queryType="2"
            - 如果是家庭圈业务(busiType=5)，需要从查询中提取成员号码列表
            """,

            "product-recommend": """
            特殊说明：
            - bizType映射：
            * 5G特惠包 = "001"
            * 5G套餐个人版 = "002"
            * 5G直通车30元档 = "003"
            * 5G Plus会员包(流量版) = "004"
            * 5G新通话 = "005"
            * 5G视频彩铃 = "006"
            - license格式：渠道编码(3位)+时间(14位)+随机数(16-32位)
            - 默认渠道编码：999
            - serviceType默认值："01"
            - 如果用户没有提供手机号，使用默认号码：13800138000
            """,

            "query-commodity-info": """
            特殊说明：
            - queryType决定查询方式：
            * 1 = 按省份代码和产品ID查询（需要provinceCode和productId）
            * 2 = 按商品统一编码查询（需要goodsId）
            * 3 = 信息核查（需要contactName和contactPhone）
            - resultType控制返回详细程度：1=基础信息, 2=详细信息, 3=完整信息
            - queryInfos是数组，支持批量查询
            - 省份代码示例：北京=010, 上海=021, 广州=020
            """,

            "opr_sms": """
            特殊说明：
            - 需要从查询中提取短信内容、接收方等信息
            - 关键词"申请短信模板"通常表示需要创建新的短信模板
            - 默认参数可能需要模板ID、短信内容、接收方号码等
            """
        }

        return tool_hints.get(tool_id, "")

    def _simple_parameter_mapping(self, input_params: Dict[str, Any], tool_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """简单的参数映射降级方案 - 增强版本"""
        mapped_params = {}

        print(f"开始简单参数映射: {input_params} -> 工具参数: {tool_parameters}")

        if not tool_parameters or 'properties' not in tool_parameters:
            # 如果没有参数定义，直接返回输入参数
            print("没有工具参数定义，直接返回输入参数")
            return input_params

        # 获取工具需要的参数
        required_params = tool_parameters.get('required', [])
        param_properties = tool_parameters.get('properties', {})

        print(f"工具需要的参数: {list(param_properties.keys())}")
        print(f"必需参数: {required_params}")

        # 尝试映射参数
        for param_name, param_info in param_properties.items():
            # 1. 首先尝试直接匹配
            if param_name in input_params:
                mapped_params[param_name] = input_params[param_name]
                print(f"直接匹配参数: {param_name}")
                continue

            # 2. 尝试通用字段映射
            common_mappings = {
                'expression': ['query', 'content', 'text', 'input'],
                'content': ['query', 'text', 'message', 'input'],
                'query': ['content', 'text', 'search', 'input'],
                'text': ['content', 'query', 'input', 'message'],
                'city': ['query', 'content', 'location'],
                'location': ['query', 'content', 'city'],
                'file': ['query', 'content', 'filename', 'path'],
                'filename': ['query', 'content', 'file', 'path'],
                'path': ['query', 'content', 'file', 'filename']
            }

            if param_name in common_mappings:
                for alt_name in common_mappings[param_name]:
                    if alt_name in input_params:
                        mapped_params[param_name] = input_params[alt_name]
                        print(f"通过映射匹配参数: {param_name} <- {alt_name}")
                        break

            # 3. 如果是必需参数但还没有映射，尝试从查询中提取
            if param_name in required_params and param_name not in mapped_params:
                # 尝试从query或content中提取
                query_text = input_params.get('query', input_params.get('content', ''))
                if query_text:
                    # 简单的关键词提取
                    if param_name == 'city' or param_name == 'location':
                        # 提取城市名
                        cities = ['北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '重庆', '天津', '武汉']
                        for city in cities:
                            if city in query_text:
                                mapped_params[param_name] = city
                                print(f"从查询中提取城市: {param_name} = {city}")
                                break
                    elif param_name in ['file', 'filename', 'path']:
                        # 提取文件名
                        import re
                        file_pattern = r'([a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,4})'
                        matches = re.findall(file_pattern, query_text)
                        if matches:
                            mapped_params[param_name] = matches[0]
                            print(f"从查询中提取文件名: {param_name} = {matches[0]}")

                    # 如果还没有映射，使用完整查询
                    if param_name not in mapped_params:
                        mapped_params[param_name] = query_text
                        print(f"使用完整查询作为参数: {param_name} = {query_text}")

        print(f"参数映射结果: {mapped_params}")
        return mapped_params

    async def _extract_parameters_with_llm(self, query: str, tool_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM从查询中提取工具参数 - 修复版本"""
        if not self.llm_client:
            logger.warning("未配置LLM客户端，无法自动提取参数")
            return self._enhanced_parameter_extraction(query, tool_parameters)

        try:
            print(f"开始LLM参数提取: query='{query}'")

            # 构建增强的参数提取prompt
            prompt_text = self._build_enhanced_parameter_extraction_prompt(query, tool_parameters)

            # 创建消息并调用LLM
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt_text)]

            # mcp工具场景，禁用llm自动emit。
            modified_config = copilotkit_customize_config(
                emit_messages=False,  # if you want to disable message streaming #
                emit_tool_calls=False  # if you want to disable tool call streaming #
            )

            # 调用LLM并处理不同类型的响应
            try:
                response = await self.llm_client.ainvoke(messages, config=modified_config)

                # 处理响应内容 - 兼容不同的响应格式
                if hasattr(response, 'content'):
                    response_content = response.content
                elif isinstance(response, str):
                    response_content = response
                elif isinstance(response, dict):
                    # 如果响应是字典，尝试获取content字段
                    response_content = response.get('content', str(response))
                else:
                    # 其他情况，转换为字符串
                    response_content = str(response)

                print(f"LLM响应类型: {type(response)}, 内容类型: {type(response_content)}")

            except Exception as llm_error:
                logger.error(f"LLM调用失败: {str(llm_error)}")
                # 如果LLM调用失败，使用降级方案
                return self._enhanced_parameter_extraction(query, tool_parameters)

            # 解析LLM响应
            extracted_params = self._parse_llm_response(response_content, tool_parameters)

            # 后处理和验证
            extracted_params = self._post_process_parameters(extracted_params, query)

            logger.info(f"LLM提取的参数: {extracted_params}")
            return extracted_params

        except Exception as e:
            logger.error(f"LLM参数提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 使用增强的降级方案
            return self._enhanced_parameter_extraction(query, tool_parameters)

    def _build_parameter_extraction_prompt(self, query: str, tool_parameters: Dict[str, Any]) -> str:
        """构建参数提取的prompt - 优化版本"""

        # 清理查询内容
        clean_query = sanitize_string_for_json(query)

        prompt = f"""
        你是一个智能参数提取助手。请从用户查询中提取工具所需的参数。

        用户查询: {clean_query}

        工具参数定义:
        """

        # 添加参数定义
        if tool_parameters and 'properties' in tool_parameters:
            for param_name, param_info in tool_parameters.get('properties', {}).items():
                # 检查param_info是否为字典，如果不是则跳过
                if not isinstance(param_info, dict):
                    # 可以选择跳过这个参数或者记录警告信息
                    print(f"警告: 参数 {param_name} 的信息不是字典类型，已跳过")
                    continue
                param_type = param_info.get('type', 'string')
                param_description = sanitize_string_for_json(param_info.get('description', ''))
                required = param_name in tool_parameters.get('required', [])

                prompt += f"- {param_name} ({param_type}): {param_description}"
                if required:
                    prompt += " [必需]"
                prompt += "\n"

        prompt += """
        请以JSON格式返回提取的参数，只返回JSON，不要添加其他说明文字。
        如果某个参数无法从查询中提取，请设置为合理的默认值或使用查询内容。

        重要提示：
        1. 对于数学表达式，请保持原始格式（如 "2+3" 而不是 "5"）
        2. 对于查询类参数，可以使用用户的完整查询内容
        3. 对于文件名参数，请从查询中提取文件名（如 "example.txt"）
        4. 对于城市/地点参数，请提取具体的城市名（如 "北京"）
        5. 确保JSON格式正确，可以被解析

        示例格式:
        {
            "param1": "extracted_value1",
            "param2": "extracted_value2"
        }
        """

        return prompt

    def _build_enhanced_parameter_extraction_prompt(self, query: str, tool_parameters: Dict[str, Any]) -> str:
        """构建增强的参数提取prompt"""

        # 获取工具特定的提示
        tool_specific_hints = self._get_tool_specific_extraction_hints(self.tool_id, tool_parameters)

        prompt = f"""
        你是一个智能参数提取助手。请从用户查询中提取工具所需的参数。

        工具ID: {self.tool_id}
        工具名称: {self.name}

        用户查询: {query}

        工具参数定义:
        """

        # 添加参数定义
        if tool_parameters and 'properties' in tool_parameters:
            for param_name, param_info in tool_parameters.get('properties', {}).items():
                # 跳过description字段，因为该字段不是参数字段
                if param_name == "description":
                    continue
                logger.info(f"_build_enhanced_parameter_extraction_prompt param_name: {param_name}. param_info: {param_info}")
                logger.info("type of param_info: {}".format(type(param_info)))
                temp_param_info = dict(param_info)

                param_type = temp_param_info.get('type', 'string')
                param_description = sanitize_string_for_json(temp_param_info.get('description', ''))
                
                # 考虑required字段为None的情况
                tool_parameters_required = tool_parameters.get('required', [])
                if tool_parameters_required:
                    required = param_name in tool_parameters_required
                else:
                    required = False

                prompt += f"- {param_name} ({param_type}): {param_description}"
                if required:
                    prompt += " [必需]"
                prompt += "\n"

        # 添加工具特定提示
        if tool_specific_hints:
            prompt += f"\n{tool_specific_hints}"

        prompt += """
        参数提取规则：
        1. 仔细分析用户查询，提取所有相关信息
        2. 使用合理的默认值填充未提供的必需参数
        3. 对于手机号，识别11位数字格式
        4. 对于业务类型，根据关键词进行映射
        5. 保持原始查询内容的完整性
        6. 如果参数包含enum枚举，请严格从提供的enum中取值，禁止自行总结或生成

        请以JSON格式返回提取的参数，只返回JSON，不要添加其他说明文字。

        示例格式:
        {
            "param1": "value1",
            "param2": "value2"
        }
        """

        return prompt

    def _parse_llm_response(self, response: str, tool_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析LLM响应，提取参数 - 修复版本"""
        try:
            import json

            # 确保response是字符串
            if not isinstance(response, str):
                response = str(response)

            print(f"开始解析LLM响应: {response[:200]}...")

            # 尝试解析JSON响应
            response = response.strip()

            # 移除可能的markdown代码块标记
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # 使用安全的JSON解析
            try:
                extracted_params = json.loads(response)

                # 确保extracted_params是字典
                if not isinstance(extracted_params, dict):
                    print(f"LLM返回的不是字典类型: {type(extracted_params)}")
                    # 如果不是字典，尝试包装成字典
                    if isinstance(extracted_params, str):
                        extracted_params = {"query": extracted_params}
                    else:
                        extracted_params = {"query": str(extracted_params)}

                print(f"JSON解析成功: {extracted_params}")

            except json.JSONDecodeError as e:
                print(f"JSON解析失败，尝试修复: {str(e)}")
                # 尝试修复常见的JSON错误
                fixed_response = self._fix_json_response(response)
                try:
                    extracted_params = json.loads(fixed_response)
                    if not isinstance(extracted_params, dict):
                        extracted_params = {"query": response}
                    print(f"修复后JSON解析成功: {extracted_params}")
                except:
                    # 如果还是失败，创建默认参数字典
                    print(f"JSON修复失败，使用默认参数")
                    extracted_params = {"query": response}

            # 验证和清理参数
            validated_params = {}
            if tool_parameters and isinstance(tool_parameters, dict) and 'properties' in tool_parameters:
                for param_name, param_info in tool_parameters.get('properties', {}).items():
                    tool_parameters_required = tool_parameters.get('required', [])
                    if tool_parameters_required:
                        required = param_name in tool_parameters_required
                    else:
                        required = False

                    if param_name in extracted_params:
                        value = extracted_params[param_name]
                        if value is not None and value != "":
                            # 清理参数值
                            if isinstance(value, str):
                                value = sanitize_string_for_json(value)
                            validated_params[param_name] = value
                        else:
                            validated_params[param_name] = value
                    # 如果是必需参数但没有提取到，尝试使用默认值
                    elif required:
                        # 根据参数类型设置默认值
                        param_type = param_info.get('type', 'string') if isinstance(param_info, dict) else 'string'
                        if param_type == 'string':
                            validated_params[param_name] = ""
                        elif param_type == 'number':
                            validated_params[param_name] = 0
                        elif param_type == 'boolean':
                            validated_params[param_name] = False
                        elif param_type == 'array':
                            validated_params[param_name] = []
                        elif param_type == 'object':
                            validated_params[param_name] = {}
            else:
                # 如果没有参数定义，直接返回提取的参数
                validated_params = deep_clean_for_json(extracted_params)

            print(f"验证后的参数: {validated_params}")
            return validated_params

        except Exception as e:
            logger.error(f"处理LLM响应失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 降级处理：返回包含查询的默认参数
            return {"query": sanitize_string_for_json(str(response))}

    def _fix_json_response(self, response: str) -> str:
        """最安全的JSON修复方案"""
        if not isinstance(response, str):
            response = str(response)

        # 🔥 最安全的方案：先尝试解析，只有失败时才修复
        try:
            # 先尝试直接解析
            json.loads(response)
            return response  # 如果成功，直接返回
        except json.JSONDecodeError:
            # 解析失败，再进行修复
            pass

        # 保存原始响应用于降级处理
        original_response = response

        # 基础清理
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        # 只进行最基本的修复

        # 1. 修复缺少结束引号
        if response.count('"') % 2 != 0:
            response += '"'

        # 2. 修复缺少结束括号
        open_braces = response.count('{')
        close_braces = response.count('}')
        if open_braces > close_braces:
            response += '}' * (open_braces - close_braces)

        # 3. 修复缺少结束方括号
        open_brackets = response.count('[')
        close_brackets = response.count(']')
        if open_brackets > close_brackets:
            response += ']' * (open_brackets - close_brackets)

        # 4. 移除尾随逗号
        response = re.sub(r',(\s*[}\]])', r'\1', response)

        # 5. 只处理明显的未加引号的值（避免破坏转义序列）
        # 这个正则表达式更加保守
        response = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,\}])', r': "\1"\2', response)

        # 最后验证修复结果
        try:
            json.loads(response)
            return response
        except json.JSONDecodeError:
            # 如果还是失败，返回原始响应，让上层处理
            return original_response

    def _enhanced_parameter_extraction(self, query: str, tool_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """增强的参数提取降级方案 - 针对特定工具优化"""

        print(f"使用增强参数提取方案: tool_id={self.tool_id}")

        # 供应链数据分析工具
        if self.tool_id == "supplychain_data_analysis":
            return {"query": query}

        # 省公司商品查询工具
        elif self.tool_id == "query_wb_goods":
            params = {
                "xsgRouteType": "01",
                "serviceType": "01",
                "queryType": "2",
                "goodsId": "",
                "memberList": [],
                "memNumber": ""
            }

            # 提取手机号
            import re
            phone_pattern = r'1[3-9]\d{9}'
            phones = re.findall(phone_pattern, query)
            if phones:
                params["serviceNumber"] = phones[0]
                params["xsgRouteValue"] = phones[0]

            # 提取业务类型
            if "宽带" in query:
                params["busiType"] = "1"
            elif "号卡" in query or "套餐" in query:
                params["busiType"] = "2"
            elif "组合包" in query:
                params["busiType"] = "3"
            elif "融合" in query:
                params["busiType"] = "4"
            elif "家庭" in query or "家庭圈" in query:
                params["busiType"] = "5"
                # 提取家庭成员号码
                if len(phones) > 1:
                    params["memberList"] = [{"memNumber": phone} for phone in phones[1:]]
                    params["memNumber"] = phones[1] if len(phones) > 1 else ""
            else:
                params["busiType"] = "1"  # 默认宽带

            return params

        # 精准营销产品推荐工具
        elif self.tool_id == "product-recommend":
            import datetime
            import random

            params = {
                "serviceType": "01"
            }

            # 提取手机号
            import re
            phone_pattern = r'1[3-9]\d{9}'
            phones = re.findall(phone_pattern, query)
            params["serviceNumber"] = phones[0] if phones else "13800138000"

            # 提取业务类型
            if "特惠包" in query:
                params["bizType"] = "001"
            elif "个人版" in query or "套餐个人" in query:
                params["bizType"] = "002"
            elif "直通车" in query or "30元" in query:
                params["bizType"] = "003"
            elif "Plus会员" in query or "流量版" in query:
                params["bizType"] = "004"
            elif "新通话" in query:
                params["bizType"] = "005"
            elif "视频彩铃" in query:
                params["bizType"] = "006"
            else:
                params["bizType"] = "001"  # 默认特惠包

            # 生成license
            channel_code = "999"
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            random_num = ''.join([str(random.randint(0, 9)) for _ in range(16)])
            params["license"] = f"{channel_code}{timestamp}{random_num}"

            return params

        # 商品信息查询工具
        elif self.tool_id == "query-commodity-info":
            params = {
                "queryInfos": [],
                "resultType": "1"
            }

            # 判断查询类型
            if "省份" in query or "产品ID" in query:
                params["queryType"] = "1"
                # 提取省份信息
                province_map = {
                    "北京": "010", "上海": "021", "广州": "020",
                    "深圳": "0755", "天津": "022", "重庆": "023"
                }
                for province, code in province_map.items():
                    if province in query:
                        params["queryInfos"].append({
                            "provinceCode": code,
                            "productId": "",  # 需要从查询中提取
                            "goodsId": "",
                            "contactName": "",
                            "contactPhone": ""
                        })

            elif "统一编码" in query or "商品编码" in query:
                params["queryType"] = "2"
                # 提取编码信息
                import re
                code_pattern = r'[A-Z0-9_]{8,}'
                codes = re.findall(code_pattern, query)
                for code in codes:
                    params["queryInfos"].append({
                        "provinceCode": "",
                        "productId": "",
                        "goodsId": code,
                        "contactName": "",
                        "contactPhone": ""
                    })

            elif "核查" in query or "联系人" in query:
                params["queryType"] = "3"
                # 提取联系人信息
                # 这里需要更复杂的NLP处理，暂时返回空
                params["queryInfos"].append({
                    "provinceCode": "",
                    "productId": "",
                    "goodsId": "",
                    "contactName": "",
                    "contactPhone": ""
                })

            # 如果没有提取到任何信息，使用默认查询
            if not params["queryInfos"]:
                params["queryType"] = "1"
                params["queryInfos"].append({
                    "provinceCode": "010",
                    "productId": "",
                    "goodsId": "",
                    "contactName": "",
                    "contactPhone": ""
                })

            return params

        # 短信发送工具
        elif self.tool_id == "opr_sms":
            params = {}

            if "申请" in query and "模板" in query:
                params["action"] = "create_template"
                params["template_content"] = query
            else:
                params["action"] = "send_sms"
                params["content"] = query

            return params

        # 默认处理
        else:
            return {"query": query}

    def _post_process_parameters(self, params: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """参数后处理，确保参数完整性和正确性"""

        # 供应链数据分析工具 - 确保query包含完整内容
        if self.tool_id == "supplychain_data_analysis":
            if "query" not in params or not params["query"]:
                params["query"] = original_query

        # 省公司商品查询 - 验证必需字段
        elif self.tool_id == "query_wb_goods":
            # 确保必需字段存在
            required_fields = ["xsgRouteType", "xsgRouteValue", "serviceType",
                               "serviceNumber", "busiType", "queryType"]
            for field in required_fields:
                if field not in params:
                    if field in ["xsgRouteType", "serviceType"]:
                        params[field] = "01"
                    elif field == "queryType":
                        params[field] = "2"
                    elif field == "busiType":
                        params[field] = "1"
                    elif field in ["xsgRouteValue", "serviceNumber"]:
                        # 如果其中一个存在，复制到另一个
                        if "serviceNumber" in params and params["serviceNumber"]:
                            params["xsgRouteValue"] = params["serviceNumber"]
                        elif "xsgRouteValue" in params and params["xsgRouteValue"]:
                            params["serviceNumber"] = params["xsgRouteValue"]

        # 精准营销产品推荐 - 验证license格式
        elif self.tool_id == "product-recommend":
            if "license" not in params or len(params.get("license", "")) < 33:
                # 重新生成有效的license
                import datetime
                import random
                channel_code = "999"
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                random_num = ''.join([str(random.randint(0, 9)) for _ in range(16)])
                params["license"] = f"{channel_code}{timestamp}{random_num}"

        # 商品信息查询 - 确保queryInfos不为空
        elif self.tool_id == "query-commodity-info":
            if "queryInfos" not in params or not params["queryInfos"]:
                params["queryInfos"] = [{
                    "provinceCode": "",
                    "productId": "",
                    "goodsId": "",
                    "contactName": "",
                    "contactPhone": ""
                }]

        return params

    def _process_knowledge_attachment_response(self, result_data: Dict[str, Any],
                                               tool_type: str) -> MCPToolExecutionResult:
        """
        处理知识库和附件工具的响应格式 - 优化版本

        Args:
            result_data: 服务器返回的数据
            tool_type: 工具类型

        Returns:
            MCPToolExecutionResult: 处理后的执行结果
        """
        try:
            print(f"\n======== 处理 {tool_type} 响应 ========")

            # 检查是否直接包含 parts 数组（新的响应格式）
            if 'parts' in result_data:
                parts = result_data.get('parts', [])

                print(f"发现 parts 数组，包含 {len(parts)} 个结果")

                if parts:
                    # 将所有检索结果组合成一个回答
                    content_parts = []
                    for i, part in enumerate(parts, 1):
                        content = part.get('content', '')
                        doc_name = part.get('docName', '未知文档')
                        score = part.get('score', 0)

                        print(f"\n--- Part {i} ---")
                        print(f"文档名: {doc_name}")
                        print(f"相关度: {score:.4f}")
                        print(f"内容长度: {len(content)} 字符")

                        # 清理内容
                        content = sanitize_string_for_json(content)

                        # 为attachment工具添加特殊标记
                        if tool_type == 'attachment':
                            content_parts.append(f"附件内容 {i} [{doc_name}] (相关度: {score:.2f}):\n{content}")
                        else:
                            content_parts.append(f"知识库内容 {i} [{doc_name}] (相关度: {score:.2f}):\n{content}")

                    combined_content = "\n\n".join(content_parts)

                    # 为attachment工具添加特殊前缀
                    if tool_type == 'attachment':
                        combined_content = f"=== 附件分析结果 ===\n{combined_content}\n=== 附件分析结束 ==="

                    print(f"\n组合后内容长度: {len(combined_content)} 字符")

                    return MCPToolExecutionResult(
                        type="text",
                        content=combined_content,
                        status=True,
                        error_msg=""
                    )
                else:
                    not_found_message = "未找到相关附件内容" if tool_type == 'attachment' else "未找到相关信息"
                    print(f"Parts 数组为空: {not_found_message}")
                    return MCPToolExecutionResult(
                        type="text",
                        content=not_found_message,
                        status=True,
                        error_msg=""
                    )
            # 兼容原有的 retcode 格式
            elif result_data.get('retcode') == 200:
                print("使用 retcode 格式处理响应")
                data = result_data.get('data', {})
                parts = data.get('parts', [])

                if parts:
                    content_parts = []
                    for i, part in enumerate(parts, 1):
                        content = sanitize_string_for_json(part.get('content', ''))
                        doc_name = part.get('docName', '未知文档')
                        score = part.get('score', 0)

                        if tool_type == 'attachment':
                            content_parts.append(f"附件内容 {i} [{doc_name}] (相关度: {score:.2f}):\n{content}")
                        else:
                            content_parts.append(f"知识库内容 {i} [{doc_name}] (相关度: {score:.2f}):\n{content}")

                    combined_content = "\n\n".join(content_parts)

                    if tool_type == 'attachment':
                        combined_content = f"=== 附件分析结果 ===\n{combined_content}\n=== 附件分析结束 ==="

                    return MCPToolExecutionResult(
                        type="text",
                        content=combined_content,
                        status=True,
                        error_msg=""
                    )
                else:
                    not_found_message = "未找到相关附件内容" if tool_type == 'attachment' else "未找到相关信息"
                    return MCPToolExecutionResult(
                        type="text",
                        content=not_found_message,
                        status=True,
                        error_msg=""
                    )
            else:
                # 如果既没有直接的parts，也没有retcode，则认为是错误
                print("响应格式无法识别")
                return MCPToolExecutionResult(
                    type="error",
                    content="",
                    status=False,
                    error_msg="无法解析知识库/附件响应格式"
                )

        except Exception as e:
            logger.error(f"处理知识库/附件响应异常: {str(e)}")
            print(f"\n======== 处理响应异常 ========")
            print(f"异常类型: {type(e).__name__}")
            print(f"异常信息: {str(e)}")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg=f"处理响应异常: {str(e)}"
            )

    async def prepare_arguments(self, state: AgentState, filtered_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备参数
        """

        # 过滤掉无关参数
        filtered_kwargs = {k: v for k, v in filtered_kwargs.items()
                            if k not in ['state', 'special_config_param'] and v is not None and v != ''}

        print(f"过滤后参数: {safe_json_dumps(filtered_kwargs, indent=2)}")

        # 处理知识库和附件类型的工具
        if self.tool_type in ["knowledge", "attachment"]:
            # 获取content参数
            content = filtered_kwargs.get("content", "")

            # 如果有state，直接从state中提取用户查询
            if state:
                user_query = extract_user_query_from_state(state)
                if user_query:
                    logger.info(f"从状态中提取到用户查询: {user_query}")
                    content = user_query
                else:
                    logger.warning("未能从状态中提取用户查询")
                    # 如果content看起来是无效的请求，使用默认值
                    invalid_patterns = ["请提供", "请告诉", "url", "路径", "文件名", "请输入", "需要"]
                    if any(pattern in content.lower() for pattern in invalid_patterns):
                        content = "请分析附件内容"
                        logger.info(f"检测到无效content，使用默认值: {content}")

            # 清理content内容
            content = sanitize_string_for_json(content)

            # 对于知识库和附件类型，添加dbList参数
            arguments = {
                "dbList": [{"name": self.tool_id}],
                "content": content
            }
            print(f"Attachment/Knowledge工具参数: {safe_json_dumps(arguments, indent=2)}")
        else:
            # 对于普通工具，使用改进的参数提取逻辑
            query = filtered_kwargs.get("query", "")
            if not query:
                # 如果没有query，尝试从其他参数中获取
                query = filtered_kwargs.get("content", "")
                if not query and filtered_kwargs:
                    # 如果还是没有，将所有参数值连接作为查询
                    query = " ".join(str(v) for v in filtered_kwargs.values() if v)

            # 如果有state且query为空，从state中提取用户查询
            if not query and state:
                user_query = extract_user_query_from_state(state)
                if user_query:
                    query = user_query
                    logger.info(f"从状态中提取到用户查询用于普通工具: {query}")

            # 如果有子任务，使用子任务
            if state.get("sub_task"):
                logger.info(f"query改为使用子任务: {state.get('sub_task')}")
                query = state.get("sub_task")

            # 清理查询内容
            query = sanitize_string_for_json(query)

            if query:
                # 获取工具的参数定义
                tool_parameters = getattr(self, '_original_parameters', {})

                if self.llm_client:
                    # 使用LLM提取参数
                    try:
                        extracted_params = await self._extract_parameters_with_llm(query, tool_parameters)
                        arguments = extracted_params
                    except Exception as e:
                        logger.warning(f"LLM参数提取失败，使用降级方案: {str(e)}")
                        # 降级方案1：使用增强的参数提取
                        arguments = self._enhanced_parameter_extraction(query, tool_parameters)
                else:
                    # 降级方案2：使用增强的参数提取
                    arguments = self._enhanced_parameter_extraction(query, tool_parameters)
            else:
                # 降级方案3：直接使用过滤后的参数
                arguments = filtered_kwargs.copy()

            # # 如果有预定义参数，合并它们（预定义参数优先级更低）
            # if self.predefined_arguments:
            #         for key, value in self.predefined_arguments.get("properties", {}).items():
            #             if key not in arguments or not arguments[key]:
            #                 arguments[key] = value

        # 清理最终参数
        arguments = deep_clean_for_json(arguments)

        return arguments

    async def _execute_mcp_tool(
        self,
        tool_name:str,
        tool_id: str,
        arguments: Dict[str, Any],
        tool_type: str = "normal",
        mcp_server_url: str = None,
        user_id: str = None) -> MCPToolExecutionResult:
        """
        执行MCP工具 - 修复版本，增强JSON处理

        Args:
            tool_id: 工具ID
            arguments: 工具参数
            tool_type: 工具类型，可选值为 "normal", "knowledge", 或 "attachment"，默认为 "normal"
            mcp_server_url: MCP服务器URL（新增）
            user_id: 用户ID（新增）

        Returns:
            MCPToolExecutionResult: 执行结果
        """
        print(f"\n======== 执行 MCP 工具 ========")
        print(f"工具ID: {tool_id}")
        print(f"工具类型: {tool_type}")
        print(f"MCP服务器URL: {mcp_server_url}")
        print(f"用户ID: {user_id}")
        print(f"执行参数: {arguments}")

        # 根据工具类型选择不同的API和数据格式
        if tool_type in ["knowledge", "attachment"]:
            # 知识库和附件工具使用特定的API和格式
            url = self.knowledge_tool_url
            payload = arguments  # 直接使用arguments，格式为 {"content": "...", "dbList": [...]}
            logger.info(f"调用知识库/附件API: {url}")
        else:
            # 普通工具使用通用的API格式
            url = self.normal_tool_url
            payload = {
                "toolId": tool_id,
                "arguments": arguments,
                "type": tool_type,
                "channelId": "work-agent"
            }

            # 为普通工具添加新字段
            if mcp_server_url:
                payload["mcpServerUrl"] = mcp_server_url
            if user_id:
                payload["userId"] = user_id

            logger.info(f"调用普通工具API: {url}")

        print(f"请求URL: {url}")

        # 使用安全的JSON序列化
        try:
            json_payload = safe_json_dumps(payload)
            print(f"序列化后的请求载荷: {json_payload}")
        except Exception as json_error:
            logger.error(f"JSON序列化失败: {str(json_error)}")
            print(f"JSON序列化失败: {str(json_error)}")

            # 调试JSON序列化问题
            debug_result = debug_json_error(payload, f"工具{tool_id}的载荷")
            if debug_result:
                json_payload = debug_result
            else:
                return MCPToolExecutionResult(
                    type="error",
                    content="",
                    status=False,
                    error_msg=f"参数序列化失败: {str(json_error)}"
                )

        # 准备headers
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }
        # 发送异步HTTP请求
        try:
            response_data = await async_http_post(url, json_payload, headers, 300)
            response = type('Response', (), {
                'status_code': response_data['status_code'],
                'headers': response_data['headers'],
                'text': response_data['text']
            })()
        except requests.Timeout:
            logger.error("MCP工具执行超时")
            print("\n======== 请求超时 ========")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg="请求超时"
            )
        except requests.RequestException as e:
            logger.error(f"MCP工具执行请求失败: {str(e)}")
            print(f"\n======== 请求异常 ========")
            print(f"异常类型: {type(e).__name__}")
            print(f"异常信息: {str(e)}")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg=f"请求失败: {str(e)}"
            )
        except Exception as http_error:
            logger.error(f"HTTP请求失败: {str(http_error)}")
            print(f"HTTP请求失败: {str(http_error)}")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg=f"HTTP请求失败: {str(http_error)}"
            )

        print(f"\n======== HTTP 响应 ========")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code != 200:
            logger.error(f"服务器返回错误: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            print(f"错误响应内容: {response.text}")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg=f"服务器返回错误: {response.status_code}, 内容: {response.text}"
            )

        # 检查响应是否为空
        if not response.text or response.headers.get('Content-Length') == '0':
            logger.warning(f"服务器返回空响应")
            print("警告：服务器返回空响应")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg="服务器返回空响应"
            )
        
        try:
            result_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.error(f"响应内容: {response.text}")
            return MCPToolExecutionResult(
                type="error",
                content="",
                status=False,
                error_msg=f"响应格式错误: {str(e)}"
            )

        # 增强调试信息：打印完整的原始响应
        print(f"\n======== 原始响应数据 ========")
        print(safe_json_dumps(result_data, indent=2))
        print("=============================")

        # 根据不同API的响应格式处理结果
        if tool_type in ["knowledge", "attachment"]:
            # 知识库和附件API的响应格式处理
            return self._process_knowledge_attachment_response(result_data, tool_type)
        else:
            # 普通工具API的响应格式处理
            content = result_data.get('content')
            if content is None:
                content = ""
                logger.warning(f"工具 {tool_id} 返回空内容")

            status = result_data.get('status', False)
            error_msg = result_data.get('errorMsg', '')

            # 如果status为False但没有错误信息，生成默认错误信息
            if not status and not error_msg:
                if content == "":
                    error_msg = "工具执行失败，未返回内容"
                else:
                    error_msg = "工具执行失败"

            return MCPToolExecutionResult(
                type=result_data.get('type', 'text'),
                content=content,
                status=status,
                error_msg=error_msg
            )
            
    async def _run(self,
        tool_id: str, 
        tool_name: str, 
        tool_type: str, 
        arguments: Dict[str, Any], 
        mcp_server_url: str, 
        user_id: str) -> MCPToolExecutionResult:
        """同步执行工具 - 修复版本：增强JSON处理和参数传递调试"""
        print(f"最终发送给 MCP 的参数: {safe_json_dumps(arguments, indent=2)}")

        # 🔥 确保参数正确传递
        print(f"\n======== 执行器调用前的参数检查 ========")
        print(f"即将传递的 mcp_server_url: {mcp_server_url}")
        print(f"即将传递的 user_id: {user_id}")

        # 执行工具
        result = await self._execute_mcp_tool(
            tool_name,
            tool_id,
            arguments,
            tool_type,
            mcp_server_url,
            user_id
        )

        # 增强调试信息：打印原始执行结果
        print(f"\n======== 工具执行结果（原始）========")
        print(f"结果类型: {result.type}")
        print(f"执行状态: {'成功' if result.status else '失败'}")
        print(f"错误信息: {result.error_msg if result.error_msg else '无'}")
        # 安全处理content可能为None的情况
        if result.content is not None:
            print(f"内容长度: {len(result.content)} 字符")
            print(f"内容预览（前1000字符）:")
            print(result.content[:1000])
            if len(result.content) > 1000:
                print("... (内容过长，已截断)")
        else:
            print("内容: None (空内容)")
        print("==================================")

        return result

    async def ainvoke(self, 
        tool_id: str, 
        tool_name: str, 
        tool_type: str, 
        arguments: Dict[str, Any], 
        mcp_server_url: str, 
        user_id: str) -> MCPToolExecutionResult:
        """
        异步调用方法，兼容AgentGraphWithMCP架构

        Args:
            arguments: 包含state和工具参数的字典
            config: 配置信息

        Returns:
            Tuple[AgentState, str]: 状态和执行结果
        """
        # 记录调用信息
        logger.info(f"工具 {tool_name} (类型: {tool_type}) 开始异步调用")

        # 执行工具（传递完整的arguments，包括state）
        result = await self._run(tool_id, tool_name, tool_type, arguments, mcp_server_url, user_id)

        logger.info(f"工具 {tool_name} 异步调用完成")

        return result


class MCPToLangGraphConverter:
    """MCP工具转LangGraph工具转换器 - 优化版本"""

    def __init__(self, llm_client=None):
        """
        初始化转换器

        Args:
            llm_client: 大模型客户端，用于结果总结和参数提取。如果为None，将自动创建默认客户端
        """
        # 如果没有提供llm_client，创建默认的
        if llm_client is None:
            logger.info("未提供LLM客户端，正在创建默认客户端...")
            self.llm_client = create_default_llm_client()
        else:
            self.llm_client = llm_client

    def create_mcp_tool_info_from_state(self, mcp_tool_data: Dict[str, Any]) -> MCPToolInfo:
        """
        从AgentState中的MCP工具数据创建MCPToolInfo对象 - 修复版本
        """
        try:
            logger.info(f"正在处理工具数据: {mcp_tool_data.get('name', 'unknown')}")

            # 提取基本信息
            tool_id = mcp_tool_data.get('tool_id') or mcp_tool_data.get('id', '')
            name = mcp_tool_data.get('name', '')
            description = mcp_tool_data.get('description') or mcp_tool_data.get('desc', '')
            tool_type = mcp_tool_data.get('type', 'normal')
            arguments = mcp_tool_data.get('arguments', [])

            # 清理描述中的特殊字符，避免JSON解析错误
            if description:
                description = sanitize_string_for_json(description)

            # 清理工具名称
            if name:
                name = sanitize_string_for_json(name)

            # 提取新增字段 - 支持多种字段名
            mcp_server_url = (
                    mcp_tool_data.get('mcpServerUrl') or
                    mcp_tool_data.get('mcp_server_url') or
                    mcp_tool_data.get('mcpserverurl')
            )
            user_id = (
                    mcp_tool_data.get('userId') or
                    mcp_tool_data.get('user_id') or
                    mcp_tool_data.get('userid')
            )

            logger.info(f"工具基本信息: ID={tool_id}, Name={name}, Type={tool_type}")
            logger.info(f"清理后的描述: {description}")
            logger.info(f"MCP服务器URL: {mcp_server_url}")
            logger.info(f"用户ID: {user_id}")

            # 验证必需字段
            if not tool_id:
                raise ValueError(f"工具ID不能为空: {name}")
            if not name:
                raise ValueError(f"工具名称不能为空: {tool_id}")

            # 处理参数结构
            parameters = {}

            # 优先使用 parameters 字段
            if 'parameters' in mcp_tool_data:
                parameters = mcp_tool_data['parameters']
            # 如果有 arguments，转换为标准的 parameters 格式
            # elif arguments and isinstance(arguments, list) and len(arguments) > 0:
            elif arguments and isinstance(arguments, dict):
                # 如果已经是标准格式，直接使用
                if 'type' in arguments and arguments['type'] == 'object':
                    parameters = arguments
                else:
                    # 否则包装成标准格式
                    parameters = {
                        "type": "object",
                        "properties": arguments.get('properties', {}),
                        "required": arguments.get('required', [])
                    }
            # 如果有 properties 字段，转换为标准格式
            elif 'properties' in mcp_tool_data:
                parameters = {
                    "type": "object",
                    "properties": mcp_tool_data['properties'],
                    "required": mcp_tool_data.get('required', [])
                }
            else:
                # 根据工具类型创建默认参数结构
                if tool_type in ['knowledge', 'attachment']:
                    parameters = {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "用户查询内容"
                            }
                        },
                        "required": ["content"]
                    }
                else:
                    parameters = {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "用户查询内容，工具将自动提取所需参数"
                            }
                        },
                        "required": ["query"]
                    }

            # 清理参数中的描述字段
            if isinstance(parameters, dict) and 'properties' in parameters:
                for prop_name, prop_info in parameters['properties'].items():
                    if isinstance(prop_info, dict) and 'description' in prop_info:
                        prop_info['description'] = sanitize_string_for_json(prop_info['description'])

            logger.info(f"创建的参数结构: {json.dumps(parameters, indent=2)[:300]}...")

            return MCPToolInfo(
                tool_id=tool_id,
                name=name,
                description=description,
                parameters=parameters,
                type=tool_type,
                arguments=arguments,  # 保留原始的 arguments 数组
                mcp_server_url=mcp_server_url,
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"创建MCP工具信息失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"创建MCP工具信息失败: {str(e)}")

    def convert_from_state_data(self, mcp_tool_data: Dict[str, Any]) -> LangGraphMCPTool:
        """
        从AgentState中的MCP工具数据转换为LangGraph工具 - 优化版本，支持新字段

        Args:
            mcp_tool_data: 从AgentState中获取的MCP工具数据

        Returns:
            LangGraphMCPTool: 转换后的LangGraph工具
        """
        try:
            tool_type = mcp_tool_data.get('type', 'normal')
            tool_name = mcp_tool_data.get('name', 'unknown')

            print(f"\n======== 转换 MCP 工具 ========")
            print(f"工具名称: {tool_name}")
            print(f"工具类型: {tool_type}")
            print(f"原始数据: {safe_json_dumps(mcp_tool_data, indent=2)[:300]}...")

            # 创建MCP工具信息
            mcp_tool_info = self.create_mcp_tool_info_from_state(mcp_tool_data)

            # print(f"MCP工具信息: {mcp_tool_info}")

            # 创建LangGraph工具，传递LLM客户端用于参数提取
            langgraph_tool = LangGraphMCPTool(mcp_tool_info, self.llm_client)

            # 保存原始参数定义以供LLM参数提取使用
            if hasattr(langgraph_tool, '_original_parameters'):
                langgraph_tool._original_parameters = mcp_tool_data.get('parameters',
                                                                        mcp_tool_data.get('arguments', {}))
            else:
                setattr(langgraph_tool, '_original_parameters',
                        mcp_tool_data.get('parameters', mcp_tool_data.get('arguments', {})))

            logger.info(f"成功转换{tool_type}工具: {mcp_tool_info.name}")

            # 为attachment工具添加特殊日志
            if mcp_tool_info.type == 'attachment':
                logger.info(f"Attachment工具 {mcp_tool_info.name} 已准备就绪，支持强制执行")

            print(f"转换成功: {tool_name}")
            print("==============================\n")

            return langgraph_tool

        except Exception as e:
            logger.error(f"转换MCP工具失败: {str(e)}")
            import traceback
            traceback.print_exc()

            print(f"\n======== 转换失败 ========")
            print(f"工具名称: {mcp_tool_data.get('name', 'unknown')}")
            print(f"错误信息: {str(e)}")
            print("========================\n")

            raise Exception(f"转换MCP工具失败: {str(e)}")

    def batch_convert_from_state(self, mcp_tools_data: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]) -> List[
        LangGraphMCPTool]:
        """
        批量从AgentState中的MCP工具数据转换为LangGraph工具 - 优化版本

        统一处理所有类型的工具，避免重复
        """
        print("\n======== 批量转换 MCP 工具 ========")

        converted_tools = []
        tool_type_counts = {'normal': 0, 'knowledge': 0, 'attachment': 0}
        failed_tools = []

        # 处理不同的输入格式
        if isinstance(mcp_tools_data, dict):
            tools_list = []
            for tool_key, tool_data in mcp_tools_data.items():
                tool_copy = tool_data.copy()
                if 'name' not in tool_copy:
                    tool_copy['name'] = tool_key
                if 'id' not in tool_copy and 'tool_id' not in tool_copy:
                    tool_copy['id'] = tool_key
                tools_list.append(tool_copy)
        else:
            tools_list = mcp_tools_data

        print(f"待转换工具总数: {len(tools_list)}")

        for idx, mcp_tool_data in enumerate(tools_list, 1):
            try:
                tool_name = mcp_tool_data.get('name', 'unknown')
                tool_type = mcp_tool_data.get('type', 'normal')

                print(f"\n--- 转换工具 {idx}/{len(tools_list)} ---")
                print(f"名称: {tool_name}")
                print(f"类型: {tool_type}")

                # 统一使用convert_from_state_data方法转换所有工具
                tool = self.convert_from_state_data(mcp_tool_data)
                converted_tools.append(tool)

                # 统计工具类型
                if tool_type in tool_type_counts:
                    tool_type_counts[tool_type] += 1

                logger.info(f"✅ 成功转换工具: {tool_name}")

            except Exception as e:
                tool_name = mcp_tool_data.get('name', 'unknown')
                logger.error(f"转换工具失败 {tool_name}: {str(e)}")
                failed_tools.append(tool_name)
                # 继续处理其他工具，不中断整个转换过程
                continue

        # 输出转换统计
        print(f"\n======== 批量转换完成 ========")
        print(f"成功转换: {len(converted_tools)} 个工具")
        print(f"工具类型统计: {safe_json_dumps(tool_type_counts)}")

        if failed_tools:
            print(f"转换失败的工具: {failed_tools}")

        print("=============================\n")

        return converted_tools

# 测试函数
def test_json_cleaning():
    """测试JSON清理功能"""
    print("\n=== 测试JSON清理功能 ===")

    # 测试字符清理
    test_cases = [
        '查询北京天气并写入"example.txt"文件',
        'This is a "quoted" string with \n newlines',
        '包含\\反斜杠和"引号"的字符串',
        '复杂指令：查询北京天气，然后写入文件example.txt，最后发送邮件',
    ]

    for test_text in test_cases:
        cleaned = sanitize_string_for_json(test_text)
        print(f"原文: {test_text}")
        print(f"清理后: {cleaned}")

        # 测试JSON序列化
        test_data = {"query": cleaned, "action": "test"}
        try:
            json_str = safe_json_dumps(test_data)
            print(f"✅ JSON序列化成功")
        except Exception as e:
            print(f"❌ JSON序列化失败: {str(e)}")
        print("-" * 50)


def create_mcp_converter_with_llm(llm_client: ChatOpenAI) -> MCPToLangGraphConverter:
    """
    创建带有LLM客户端的MCP转换器

    Args:
        llm_client: LLM客户端，用于参数提取

    Returns:
        MCPToLangGraphConverter: 配置了LLM客户端的转换器
    """
    return MCPToLangGraphConverter(
        llm_client=llm_client
    )



# 使用示例
if __name__ == "__main__":
    # 运行测试
    test_json_cleaning()

    # 创建转换器，不传入LLM客户端，使用默认的
    converter = MCPToLangGraphConverter()

    # 示例: 复杂指令工具测试
    complex_tool_data = {
        "tool_id": "weather_file_tool",
        "name": "天气查询并文件操作",
        "desc": "查询天气信息并将结果写入文件",
        "type": "normal",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "要查询天气的城市名称"
                },
                "filename": {
                    "type": "string",
                    "description": "要写入的文件名"
                }
            },
            "required": ["city", "filename"]
        },
        # 添加新字段测试
        "userId": "test_user_123",
        "mcpServerUrl": "http://test-mcp-server.com"
    }

    try:
        print("\n=== 测试复杂工具转换 ===")
        complex_tool = converter.convert_from_state_data(complex_tool_data)
        print(f"复杂工具转换成功: {complex_tool.name}")

        # 测试复杂指令
        print("\n=== 测试复杂指令处理 ===")
        complex_query = '查询北京天气并写入"example.txt"文件'
        result = complex_tool._run(query=complex_query)
        print(f"复杂指令执行结果: {result}")

    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback

        traceback.print_exc()