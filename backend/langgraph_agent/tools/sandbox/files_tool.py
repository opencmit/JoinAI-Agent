from copilotkit.langchain import copilotkit_emit_state

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Tuple
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id
import os

class FileInput(BaseModel):
    file_path: str = Field(description="文件路径，相对于workspace目录")
    content: str = Field(description="文件内容")

class CreateFileInput(FileInput):
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class ReadFileInput(BaseModel):
    file_path: str = Field(description="要读取的文件路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class FullFileRewriteInput(BaseModel):
    file_path: str = Field(description="要完全重写的文件路径，相对于workspace目录")
    content: str = Field(description="文件的新内容，将完全替换现有内容")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class DeleteFileInput(BaseModel):
    file_path: str = Field(description="要删除的文件路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class StrReplaceInput(BaseModel):
    file_path: str = Field(description="要替换内容的文件路径，相对于workspace目录")
    old_str: str = Field(description="要替换的文本（必须在文件中只出现一次）")
    new_str: str = Field(description="替换后的新文本")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class ListFilesInput(BaseModel):
    directory: Optional[str] = Field(default=".", description="要列出文件的目录路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class MakeDirectoryInput(BaseModel):
    directory: str = Field(description="要创建的目录路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class WriteMultipleFilesInput(BaseModel):
    files: List[FileInput] = Field(description="要创建的文件列表，每个文件包含path和content字段")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class WatchDirectoryInput(BaseModel):
    directory: Optional[str] = Field(default=".", description="要监视的目录路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

# 新增统一的文件操作工具输入模型
class FilesToolInput(BaseModel):
    operation: str = Field(description="文件操作类型，可选值: create, read, list, delete, write, mkdir, str_replace, watch, batch_write")
    path: Optional[str] = Field(None, description="文件或目录路径")
    content: Optional[str] = Field(None, description="文件内容，适用于create和write操作")
    old_str: Optional[str] = Field(None, description="要替换的字符串，适用于replace操作")
    new_str: Optional[str] = Field(None, description="替换后的字符串，适用于replace操作")
    files: Optional[List[Dict[str, str]]] = Field(None, description="文件列表，适用于batch_write操作")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")


class SandboxFilesTool:
    """统一的沙箱文件操作工具类"""
    
    # 允许直接读写和修改的文件扩展名列表
    ALLOWED_EXTENSIONS = [
        '.py', '.txt', '.md', '.json', '.yml', '.yaml', '.sh', '.csv',
        '.js', '.ts', '.html', '.css', '.go', '.java', '.c', '.cpp' # 添加一些其他常见的代码和文本文件格式
    ]
    
    def __init__(self):
        """初始化沙箱文件工具"""
        pass
    
    @staticmethod
    async def _add_log(state: AgentState, message: str, config: RunnableConfig) -> int:
        """添加日志并返回日志索引"""
        state["logs"] = state.get("logs", [])
        log_index = len(state["logs"])
        state["logs"].append({
            "message": message,
            "done": False,
            "messageId":  get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        return log_index
    
    @staticmethod
    async def _complete_log(state: AgentState, log_index: int, config: RunnableConfig):
        """完成日志"""
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
    
    @staticmethod
    async def _get_sandbox(state: AgentState):
        """获取沙箱实例"""
        return await sbx_manager.get_sandbox_async(state)
    
    @staticmethod
    def _is_allowed_extension(file_path: str) -> bool:
        """检查文件扩展名是否在允许列表中"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in SandboxFilesTool.ALLOWED_EXTENSIONS
    
    @staticmethod
    async def create_file(path: str, content: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """创建文件"""
        if not SandboxFilesTool._is_allowed_extension(path):
            return state, f"不允许创建或修改的文件格式: '{os.path.splitext(path)[1]}'. 允许的格式有: {', '.join(SandboxFilesTool.ALLOWED_EXTENSIONS)}"
        
        log_index = await SandboxFilesTool._add_log(state, f"📝 创建文件: '{path}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            await sandbox.files.write(path, content)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件 '{path}' 创建成功"
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件创建失败: {str(e)}"
    
    @staticmethod
    async def read_file(path: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """读取文件内容"""
        import os # 确保 os 模块已导入
        if not SandboxFilesTool._is_allowed_extension(path):
            return state, f"不允许读取的文件格式: '{os.path.splitext(path)[1]}'. 允许的格式有: {', '.join(SandboxFilesTool.ALLOWED_EXTENSIONS)}"
            
        log_index = await SandboxFilesTool._add_log(state, f"📖 读取文件: '{path}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            if not await sandbox.files.exists(path):
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件 '{path}' 不存在"
            
            try:
                content = await sandbox.files.read(path)
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件内容:\n{content}"
            except UnicodeDecodeError:
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件 '{path}' 是二进制文件，无法以文本形式读取"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件读取失败: {str(e)}"
    
    @staticmethod
    async def write_file(path: str, content: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """重写文件内容"""
        import os # 确保 os 模块已导入
        if not SandboxFilesTool._is_allowed_extension(path):
            return state, f"不允许重写的文件格式: '{os.path.splitext(path)[1]}'. 允许的格式有: {', '.join(SandboxFilesTool.ALLOWED_EXTENSIONS)}"
            
        log_index = await SandboxFilesTool._add_log(state, f"📄 重写文件: '{path}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            # 无需判断文件是否存在，sandbox.files.write会自动创建并写入
            
            await sandbox.files.write(path, content)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件 '{path}' 完全重写成功"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件重写失败: {str(e)}"
    
    @staticmethod
    async def delete_file(path: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """删除文件"""
        log_index = await SandboxFilesTool._add_log(state, f"🗑️ 删除文件: '{path}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            if not await sandbox.files.exists(path):
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件 '{path}' 不存在"
            
            await sandbox.files.remove(path)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件 '{path}' 删除成功"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件删除失败: {str(e)}"
    
    @staticmethod
    async def list_files(directory: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """列出目录中的文件"""
        log_index = await SandboxFilesTool._add_log(state, f"📋 列出目录: '{directory}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            if not await sandbox.files.exists(directory):
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"目录 '{directory}' 不存在"
            
            files = await sandbox.files.list(directory)
            
            file_list = []
            for file_info in files:
                file_type = "📁 " if file_info.type == "dir" else "📄 "
                file_list.append(f"{file_type}{file_info.name}")
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            
            if not file_list:
                return state, f"目录 '{directory}' 为空"
            
            return state, f"目录 '{directory}' 的内容:\n" + "\n".join(file_list)
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"列出文件失败: {str(e)}"
    
    @staticmethod
    async def make_directory(directory: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """创建目录"""
        log_index = await SandboxFilesTool._add_log(state, f"📁 创建目录: '{directory}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            result = await sandbox.files.make_dir(directory)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            
            if result:
                return state, f"目录 '{directory}' 创建成功"
            else:
                return state, f"目录 '{directory}' 已经存在"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"创建目录失败: {str(e)}"
    
    @staticmethod
    async def batch_write_files(files: List[Dict[str, str]], state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """批量写入文件"""
        import os # 确保 os 模块已导入
        # 检查批量写入的每个文件
        for file_info in files:
            if not file_info.get("file_path") or not file_info.get("content"):
                 # 这个错误检查保留
                raise ValueError("每个文件条目必须包含'file_path'和'content'字段", file_info)
            if not SandboxFilesTool._is_allowed_extension(file_info["file_path"]):
                return state, f"批量写入中包含不允许的文件格式: '{os.path.splitext(file_info['file_path'])[1]}'. 允许的格式有: {', '.join(SandboxFilesTool.ALLOWED_EXTENSIONS)}"

        log_index = await SandboxFilesTool._add_log(state, f"📝 批量创建文件: {len(files)}个文件", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            file_entries = []
            for file_info in files:
                if not file_info.get("file_path") or not file_info.get("content"):
                    raise ValueError("每个文件条目必须包含'file_path'和'content'字段", file_info)
                file_entries.append({
                    'path': file_info["file_path"],
                    'data': file_info["content"]
                })
            
            await sandbox.files.write(file_entries)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            
            file_paths = [f["file_path"] for f in files]
            return state, f"批量创建文件成功: {', '.join(file_paths)}"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"批量创建文件失败: {str(e)}"
    
    @staticmethod
    async def watch_directory(directory: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """监视目录变化"""
        log_index = await SandboxFilesTool._add_log(state, f"👀 监视目录: '{directory}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            if not await sandbox.files.exists(directory):
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"目录 '{directory}' 不存在"
            
            changes = []
            
            async def on_event(event):
                changes.append(event)
            
            handle = await sandbox.files.watch_dir(directory, on_event)
            
            import asyncio
            await asyncio.sleep(2)
            
            await handle.stop()
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            
            if not changes:
                return state, f"在目录 '{directory}' 中没有检测到变化"
            
            change_list = []
            for change in changes:
                change_type = change.type  # created, modified, deleted
                path = change.path
                change_list.append(f"{change_type}: {path}")
            
            return state, f"目录 '{directory}' 的变化:\n" + "\n".join(change_list)
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"监视目录失败: {str(e)}"
    
    @staticmethod
    async def str_replace(file_path: str, old_str: str, new_str: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """替换文件中的文本"""
        import os # 确保 os 模块已导入
        if not SandboxFilesTool._is_allowed_extension(file_path):
            return state, f"不允许修改的文件格式: '{os.path.splitext(file_path)[1]}'. 允许的格式有: {', '.join(SandboxFilesTool.ALLOWED_EXTENSIONS)}"
            
        log_index = await SandboxFilesTool._add_log(state, f"🔄 替换文件内容: '{file_path}'", config)
        
        try:
            state, sandbox = await SandboxFilesTool._get_sandbox(state)
            
            if not await sandbox.files.exists(file_path):
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件 '{file_path}' 不存在"
            
            content = await sandbox.files.read(file_path)
            
            occurrences = content.count(old_str)
            if occurrences == 0:
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"文件中未找到要替换的文本 '{old_str}'"
            
            if occurrences > 1:
                lines = [i+1 for i, line in enumerate(content.split('\n')) if old_str in line]
                await SandboxFilesTool._complete_log(state, log_index, config)
                return state, f"要替换的文本在文件中出现了多次（第{lines}行），请确保替换文本是唯一的"
            
            new_content = content.replace(old_str, new_str)
            await sandbox.files.write(file_path, new_content)
            
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文件 '{file_path}' 中的文本替换成功"
                
        except Exception as e:
            await SandboxFilesTool._complete_log(state, log_index, config)
            return state, f"文本替换失败: {str(e)}"
    
    @staticmethod
    @tool("files", args_schema=FilesToolInput)
    async def files_tool(
        operation: str,
        path: Optional[str] = None,
        content: Optional[str] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        files: Optional[List[Dict[str, str]]] = None,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> Tuple[AgentState, str]:
        """
        统一的文件操作工具，支持以下操作：
        - create: 创建文件
        - read: 读取文件内容
        - write: 重写文件内容
        - delete: 删除文件
        - list: 列出目录内容
        - mkdir: 创建目录
        - str_replace: 替换文件中的文本
        - watch: 监视目录变化
        - batch_write: 批量写入文件
        """
        config = special_config_param or RunnableConfig()
        
        if operation == "create":
            if not path or not content:
                return state, "创建文件操作需要提供path和content参数"
            return await SandboxFilesTool.create_file(path, content, state, config)
        
        elif operation == "read":
            if not path:
                return state, "读取文件操作需要提供path参数"
            return await SandboxFilesTool.read_file(path, state, config)
        
        elif operation == "write":
            if not path or not content:
                return state, "重写文件操作需要提供path和content参数"
            return await SandboxFilesTool.write_file(path, content, state, config)
        
        elif operation == "delete":
            if not path:
                return state, "删除文件操作需要提供path参数"
            return await SandboxFilesTool.delete_file(path, state, config)
        
        elif operation == "list":
            directory = path or "."
            return await SandboxFilesTool.list_files(directory, state, config)
        
        elif operation == "mkdir":
            if not path:
                return state, "创建目录操作需要提供path参数"
            return await SandboxFilesTool.make_directory(path, state, config)
        
        elif operation == "str_replace":
            if not path or old_str is None or new_str is None:
                return state, "替换文本操作需要提供path、old_str和new_str参数"
            return await SandboxFilesTool.str_replace(path, old_str, new_str, state, config)
        
        elif operation == "watch":
            directory = path or "."
            return await SandboxFilesTool.watch_directory(directory, state, config)
        
        elif operation == "batch_write":
            if not files:
                return state, "批量写入文件操作需要提供files参数"
            return await SandboxFilesTool.batch_write_files(files, state, config)
        
        else:
            return state, f"不支持的文件操作: {operation}"

files_tool = SandboxFilesTool.files_tool

async def test_tools_invoke():
    """使用工具调用API测试工具函数"""
    print("开始测试沙箱文件工具的工具调用API...")
    import traceback
    
    # 创建一个初始状态
    state = AgentState(
        input_data={},
        max_iterations=5,
        messages=[],
        temporary_message_content_list=[],
        iteration_count=0,
        logs=[],
        e2b_sandbox_id="test_sandbox",
        copilotkit={"actions": []},
        temporary_images=[],
        structure_tool_results={},
        completed=False,
        mcp_tools=[],
        model="test"
    )
    
    try:
        # 测试统一文件工具 - 创建目录
        print("\n1. 测试统一文件工具 - 创建目录:")
        make_dir_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "mkdir", 
                "path": "cjk_test_dir",
                "state": state
            }
        )
        print(f"结果: {make_dir_result}")
        
        # 测试统一文件工具 - 创建文件
        print("\n2. 测试统一文件工具 - 创建文件:")
        create_file_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "create", 
                "path": "unified_test_dir/test.txt", 
                "content": "这是通过统一工具创建的测试文件", 
                "state": state
            }
        )
        print(f"结果: {create_file_result}")
        
        # 测试统一文件工具 - 读取文件
        print("\n3. 测试统一文件工具 - 读取文件:")
        read_file_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "read", 
                "path": "unified_test_dir/test.txt", 
                "state": state
            }
        )
        print(f"结果: {read_file_result}")
        
        # 测试统一文件工具 - 替换文本
        print("\n4. 测试统一文件工具 - 替换文本:")
        replace_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "str_replace", 
                "path": "unified_test_dir/test.txt", 
                "old_str": "通过统一工具创建", 
                "new_str": "替换后", 
                "state": state
            }
        )
        print(f"结果: {replace_result}")
        
        # 测试统一文件工具 - 列出文件
        print("\n5. 测试统一文件工具 - 列出文件:")
        list_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "list", 
                "path": "unified_test_dir", 
                "state": state
            }
        )
        print(f"结果: {list_result}")
        
        # 测试统一文件工具 - 批量写入文件
        print("\n6. 测试统一文件工具 - 批量写入文件:")
        batch_write_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "batch_write", 
                "files": [
                {"file_path": "unified_test_dir/file1.txt", "content": "文件1内容"},
                {"file_path": "unified_test_dir/file2.txt", "content": "文件2内容"}
                ], 
                "state": state
            }
        )
        print(f"结果: {batch_write_result}")
        
        # 测试统一文件工具 - 监视目录
        print("\n7. 测试统一文件工具 - 监视目录:")
        watch_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "watch", 
                "path": "unified_test_dir", 
                "state": state
            }
        )
        print(f"结果: {watch_result}")
        
        # 测试统一文件工具 - 删除文件
        print("\n8. 测试统一文件工具 - 删除文件:")
        delete_result = await SandboxFilesTool.files_tool.ainvoke(
            {
                "operation": "delete", 
                "path": "unified_test_dir/test.txt", 
                "state": state
            }
        )
        print(f"结果: {delete_result}")
        
        print("\n测试完成: 统一文件工具测试成功!")
        
        print("\n所有工具调用API测试完成!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()
    # 打印最终状态
    print("\n最终状态:")
    if hasattr(state, 'logs') and state.logs:
        for i, log in enumerate(state.logs):
            print(f"Log {i+1}: {log['message']} - 完成状态: {log['done']}")
    else:
        print("没有日志记录")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools_invoke())
