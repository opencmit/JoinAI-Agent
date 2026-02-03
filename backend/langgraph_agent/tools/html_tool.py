import os
import re


from langchain_openai import ChatOpenAI
from langchain.tools.base import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from langgraph_agent.graph.state import AgentState
from langgraph_agent.utils.tool_utils import fix_markdown_display, process_raw_html_content




async def html_generation_node(
        state: AgentState,
        config: RunnableConfig,
) -> AgentState:
    """
    处理HTML生成请求，生成HTML文件并保存 - 集成内容提取功能的版本
    """
    print("=== HTML Generation Node 开始 ===")

    # 🔥 检查是否已处理，避免重复处理
    if state.get("html_generation_processed", False):
        print("HTML生成已处理，跳过")
        return state

    # 获取用户的完整查询
    user_query = ""
    for message in reversed(state.get("messages", [])):
        if hasattr(message, 'type') and message.type == "human":
            user_query = message.content
            break

    print(f"用户查询: {user_query}")

    # 使用LLM客户端
    model_name = os.getenv('HTML_BASE_LLM', 'DeepSeek-R1')
    llm_client = ChatOpenAI(
        api_key=os.getenv('HTML_OPENAI_API_KEY', 'sk-ef6a231232834ee7ab363c1269d2eb4e'),
        base_url=os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com'),
        model=model_name,
        temperature=0.1,
    )

    try:
        # 直接使用用户原始查询生成HTML
        html_messages = [
            HumanMessage(content=user_query)
        ]

        html_response = await safe_llm_invoke(llm_client, config, model_name, html_messages)
        raw_content = html_response.content

        print(f"LLM生成的原始内容长度: {len(raw_content)} 字符")

        # 🔥 关键改进：使用内容提取函数处理原始内容
        response_content, filename = await process_raw_html_content(
            raw_content, state, config, user_query
        )

        # 添加响应消息
        state["messages"].append(AIMessage(content=response_content))

        # 🔥 关键修复：标记已处理
        state["html_generation_processed"] = True
        state["force_attachment_call"] = False
        state["completed"] = True

    except Exception as e:
        print(f"HTML生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

        error_response = f"""❌ **HTML生成处理失败**

错误信息: {str(e)}

请检查您的请求并重试。您可以尝试：
1. 更具体地描述您需要的HTML页面
2. 说明页面的主要功能和内容
3. 提供设计参考或风格要求"""

        state["messages"].append(AIMessage(content=error_response))
        state["html_generation_processed"] = True

    print("=== HTML Generation Node 完成 ===")
    return state


async def markdown_to_html_node(
        state: AgentState,
        config: RunnableConfig,
) -> AgentState:
    """
    处理markdown生成请求，生成HTML文件并保存

    Args:
        state: 当前状态
        config: 运行配置

    Returns:
        AgentState: 更新后的状态
    """
    print("=== Markdown to HTML Node 开始 ===")

    # 获取用户的完整查询
    user_query = ""
    for message in reversed(state.get("messages", [])):
        if hasattr(message, 'type') and message.type == "human":
            user_query = message.content
            break

    print(f"用户查询: {user_query}")

    model_name = state.get("model")

    # 使用LLM客户端
    from langgraph_agent.graph.graph import AgentGraph
    agent_graph = AgentGraph()
    llm_client, _ = agent_graph._get_llm_client(state, config)

    try:
        # 第一步：解析用户需求，提取markdown内容
        parse_prompt = f"""请分析以下用户请求，提取其中关于markdown文件的需求。

用户请求：{user_query}

请提取以下信息：
1. markdown文件的主题或标题
2. markdown应包含的主要内容要点
3. 任何特定的格式要求

请以JSON格式返回，例如：
{{
    "title": "文档标题",
    "content_points": ["要点1", "要点2", "要点3"],
    "format_requirements": "格式要求描述"
}}"""

        parse_messages = [
            SystemMessage(content="你是一个专业的内容分析助手，擅长理解用户需求并提取关键信息。"),
            HumanMessage(content=parse_prompt)
        ]

        parse_response = await safe_llm_invoke(llm_client, config, model_name, parse_messages)

        # 尝试解析JSON响应
        import json
        import re

        # 提取JSON内容
        json_match = re.search(r'\{[\s\S]*\}', parse_response.content)
        if json_match:
            try:
                parsed_info = json.loads(json_match.group())
            except:
                # 如果JSON解析失败，使用默认值
                parsed_info = {
                    "title": "Markdown文档",
                    "content_points": [user_query],
                    "format_requirements": "标准markdown格式"
                }
        else:
            parsed_info = {
                "title": "Markdown文档",
                "content_points": [user_query],
                "format_requirements": "标准markdown格式"
            }

        print(f"解析的信息: {parsed_info}")

        # 第二步：生成markdown内容
        markdown_prompt = f"""请根据以下信息生成一个完整的markdown文档：

标题：{parsed_info.get('title', 'Markdown文档')}
内容要点：{', '.join(parsed_info.get('content_points', [user_query]))}
格式要求：{parsed_info.get('format_requirements', '标准markdown格式')}

请生成一个结构清晰、内容丰富的markdown文档。包括适当的标题层级、列表、代码块（如果需要）等markdown元素。

直接返回markdown内容，不要包含额外的说明。"""

        markdown_messages = [
            SystemMessage(content="你是一个专业的技术文档编写助手，擅长创建结构化的markdown文档。"),
            HumanMessage(content=markdown_prompt)
        ]

        markdown_response = await safe_llm_invoke(llm_client, config, model_name, markdown_messages)
        original_markdown_content = markdown_response.content

        print(f"生成的Markdown长度: {len(original_markdown_content)} 字符")

        # 第三步：将markdown转换为完整的HTML文件
        html_prompt = f"""请将以下markdown内容转换为一个完整的、可直接运行的HTML文件。

Markdown内容：
{original_markdown_content}

要求：
1. 生成完整的HTML5文档结构（包含<!DOCTYPE html>, <html>, <head>, <body>等）
2. 在<head>中包含适当的meta标签（charset, viewport等）
3. 添加美观的CSS样式，包括：
   - 响应式设计
   - 代码高亮样式
   - 表格样式
   - 引用块样式
   - 列表样式
4. 如果有代码块，添加语法高亮支持
5. 使用现代、清晰的排版风格
6. 添加适当的内边距和外边距
7. 使用易读的字体和颜色方案

直接返回完整的HTML代码，不要包含markdown代码块标记。"""

        html_messages = [
            SystemMessage(content="你是一个专业的前端开发者，擅长将markdown转换为美观的HTML页面。"),
            HumanMessage(content=html_prompt)
        ]

        html_response = await safe_llm_invoke(llm_client, config, model_name, html_messages)
        html_content = html_response.content

        # 清理HTML内容（移除可能的代码块标记）
        html_content = html_content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        print(f"生成的HTML长度: {len(html_content)} 字符")

        # 第四步：使用文件工具保存HTML文件
        # 生成文件名
        import time
        timestamp = int(time.time())
        safe_title = parsed_info.get('title', 'document').replace(' ', '_').replace('/', '_')[:50]
        filename = f"{safe_title}_{timestamp}.html"

        # 判断是否有沙箱环境
        try:
            # 调用文件工具保存文件
            from langgraph_agent.tools import files_tool

            # 准备文件工具的参数
            tool_args = {
                "operation": "create",
                "path": filename,
                "content": html_content,
                "state": state,
                "special_config_param": {"encoding": "utf-8"}
            }

            # 执行文件保存
            print(f"正在保存HTML文件: {filename}")
            result_state, save_result = await files_tool.ainvoke(tool_args, config=config)

            # 更新状态
            state = result_state

            # 构建响应消息
            if "成功" in str(save_result) or "created" in str(save_result).lower():
                # 为显示准备内容
                display_markdown = fix_markdown_display(original_markdown_content)
                response_content = f"""✅ **Markdown转HTML任务完成**

**原始需求**: {user_query}

**生成的文档信息**:
- 标题: {parsed_info.get('title', 'Markdown文档')}
- Markdown长度: {len(original_markdown_content)} 字符
- HTML文件大小: {len(html_content)} 字符

**文件已保存**:
- 文件名: `{filename}`
- 位置: 文件系统根目录

**Markdown内容预览**:
```markdown
{display_markdown[:500]}...
```

**HTML内容预览** (前500字符):
```html
{html_content[:500]}...
```

您可以通过文件工具查看或下载完整的HTML文件。"""
            else:
                # 文件保存失败，提供备用方案
                display_markdown = fix_markdown_display(original_markdown_content)
                response_content = f"""⚠️ **Markdown转HTML任务完成（文件保存失败）**

由于沙箱环境问题，文件保存失败。但HTML内容已成功生成。

**生成的文档信息**:
- 标题: {parsed_info.get('title', 'Markdown文档')}
- Markdown长度: {len(original_markdown_content)} 字符
- HTML文件大小: {len(html_content)} 字符

**完整的Markdown内容**:
```markdown
{display_markdown}
```

**完整的HTML内容**:
```html
{html_content}
```

您可以：
1. 复制上述HTML内容
2. 手动保存为 `{filename}`
3. 在浏览器中打开查看效果"""

        except Exception as file_error:
            print(f"文件保存失败: {str(file_error)}")

            # 如果文件工具失败，返回完整内容
            display_markdown = fix_markdown_display(original_markdown_content)
            response_content = f"""⚠️ **Markdown转HTML任务完成（保存失败）**

HTML内容已生成，但无法保存文件：{str(file_error)}

**生成的Markdown内容**:
```markdown
{display_markdown}
```

**生成的HTML内容**:
```html
{html_content}
```

请手动复制并保存为 `{filename}`。"""

        # 添加响应消息
        state["messages"].append(AIMessage(content=response_content))

        # 标记markdown请求已处理
        state["markdown_processed"] = True
        state["force_attachment_call"] = False  # 确保不会触发attachment处理

    except Exception as e:
        print(f"Markdown处理失败: {str(e)}")
        import traceback
        traceback.print_exc()

        error_response = f"""❌ **Markdown转HTML处理失败**

错误信息: {str(e)}

请检查您的请求并重试。"""

        state["messages"].append(AIMessage(content=error_response))
        state["markdown_processed"] = True

    print("=== Markdown to HTML Node 完成 ===")
    return state


async def enhanced_markdown_to_html_node(
        state: AgentState,
        config: RunnableConfig,
) -> AgentState:
    """
    增强版：处理包含数据分析的markdown生成请求 - 集成HTML提取功能
    """
    print("=== Enhanced Markdown to HTML Node 开始 ===")

    # 检查是否已处理
    if state.get("markdown_processed", False):
        print("Markdown处理已完成，跳过")
        return state

    # 检查HTML是否已经生成
    html_already_generated = state.get("html_generation_processed", False)

    # 获取用户的完整查询
    user_query = ""
    for message in reversed(state.get("messages", [])):
        if hasattr(message, 'type') and message.type == "human":
            user_query = message.content
            break

    print(f"用户查询长度: {len(user_query)} 字符")

    model_name = os.getenv('HTML_BASE_LLM', 'DeepSeek-R1')

    # 使用LLM客户端
    llm_client = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY', 'sk-ef6a231232834ee7ab363c1269d2eb4e'),
        base_url=os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com'),
        model=model_name,
        temperature=0.1,
    )

    try:
        # 检测是否包含数据表格
        has_data_table = any(keyword in user_query for keyword in ['rpm', 'tpm', '数据', '表格', '统计'])

        # 生成Markdown内容的逻辑（保持原有逻辑）
        if has_data_table:
            # 数据分析相关的处理...
            pass

        # 生成markdown
        markdown_messages = [
            SystemMessage(content="你是一个专业的技术文档和数据分析报告编写专家。"),
            HumanMessage(content=user_query)
        ]

        markdown_response = await safe_llm_invoke(llm_client, config, model_name, markdown_messages)
        original_markdown_content = markdown_response.content

        print(f"生成的Markdown长度: {len(original_markdown_content)} 字符")

        # 🔥 关键改进：如果需要生成HTML，使用提取函数处理
        html_response_content = ""
        if not html_already_generated:
            print("HTML未生成，开始生成HTML内容")

            # 生成HTML的提示词
            html_prompt = f"""将以下markdown转换为HTML页面：

{original_markdown_content}

请生成完整可用的HTML代码。"""

            html_messages = [
                SystemMessage(content="你是一个前端开发专家，擅长创建交互式数据可视化页面。"),
                HumanMessage(content=html_prompt)
            ]

            html_response = await safe_llm_invoke(llm_client, config, model_name, html_messages)
            raw_html_content = html_response.content

            # 🔥 使用提取函数处理HTML内容
            html_response_content, html_filename = await process_raw_html_content(
                raw_html_content, state, config, f"markdown_to_html_{user_query[:20]}"
            )

        # 保存Markdown文件
        try:
            from langgraph_agent.tools import files_tool

            # 生成Markdown文件名
            import time
            timestamp = int(time.time())
            safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', user_query[:30])
            md_filename = f"{safe_title}_{timestamp}.md"

            # 保存Markdown文件
            md_tool_args = {
                "operation": "create",
                "path": md_filename,
                "content": original_markdown_content,
                "state": state,
                "special_config_param": {"encoding": "utf-8"}
            }

            result_state, md_save_result = await files_tool.ainvoke(md_tool_args, config=config)
            state = result_state

            # 构建最终响应
            md_success = "成功" in str(md_save_result) or "created" in str(md_save_result).lower()

            if md_success:
                if not html_already_generated and html_response_content:
                    # Markdown和HTML都成功
                    response_content = f"""✅ **Markdown和HTML文件生成完成**

**Markdown文件**: `{md_filename}` ✅

{html_response_content}

**Markdown内容预览**:
```markdown
{fix_markdown_display(original_markdown_content[:300])}...
```"""
                else:
                    # 只有Markdown成功
                    response_content = f"""✅ **Markdown文档生成完成**

**Markdown文件**: `{md_filename}` ✅
**HTML文件**: 已由HTML生成器处理

**Markdown内容预览**:
```markdown
{fix_markdown_display(original_markdown_content[:500])}...
```"""
            else:
                # Markdown保存失败
                response_content = f"""⚠️ **Markdown保存失败但内容已生成**

**保存结果**: {md_save_result}

{html_response_content if html_response_content else ""}

**生成的Markdown内容**:
```markdown
{fix_markdown_display(original_markdown_content)}
```"""

        except Exception as file_error:
            print(f"Markdown文件保存失败: {str(file_error)}")
            response_content = f"""❌ **Markdown文件保存异常**

**错误信息**: {str(file_error)}

{html_response_content if html_response_content else ""}

**生成的Markdown内容**:
```markdown
{fix_markdown_display(original_markdown_content)}
```"""

        # 添加响应消息
        state["messages"].append(AIMessage(content=response_content))

        # 标记已处理
        state["markdown_processed"] = True
        state["force_attachment_call"] = False

    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()

        error_response = f"""❌ **处理失败**

错误信息: {str(e)}

请检查您的请求并重试。"""

        state["messages"].append(AIMessage(content=error_response))
        state["markdown_processed"] = True

    print("=== Enhanced Markdown to HTML Node 完成 ===")
    return state