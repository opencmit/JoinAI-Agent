"""
测试 docker-compose 启动的 LangGraph API 服务
支持多种测试场景：健康检查、图端点、流式响应等
"""

import requests
import json
import time
import sys
from typing import Optional, Dict, Any
from datetime import datetime


class DockerComposeServiceTester:
    """Docker Compose 服务测试类"""
    
    def __init__(self, base_url: str = "http://localhost:18100", timeout: int = 30):
        """
        初始化测试器
        
        Args:
            base_url: 服务基础 URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def print_header(self, title: str):
        """打印测试标题"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"ℹ️  {message}")
    
    def test_service_health(self) -> bool:
        """
        测试服务健康状态
        
        Returns:
            bool: 服务是否健康
        """
        self.print_header("1. 服务健康检查")
        
        try:
            # 尝试访问根路径或健康检查端点
            endpoints_to_try = [
                f"{self.base_url}/health",
                f"{self.base_url}/",
                f"{self.base_url}/docs",  # FastAPI docs
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(endpoint, timeout=5)
                    if response.status_code in [200, 404]:  # 404 也算服务在运行
                        self.print_success(f"服务可访问: {endpoint} (状态码: {response.status_code})")
                        return True
                except requests.exceptions.RequestException:
                    continue
            
            self.print_error("无法连接到服务")
            return False
            
        except Exception as e:
            self.print_error(f"健康检查失败: {str(e)}")
            return False
    
    def test_graph_endpoints(self) -> bool:
        """
        测试 LangGraph API 标准端点（使用 /assistants, /threads, /runs）
        
        Returns:
            bool: 端点是否可用
        """
        self.print_header("2. LangGraph API 标准端点测试")
        self.print_info("使用 LangGraph API 标准端点（/assistants, /threads, /runs）")
        
        graph_id = "agent"  # 对应 docker-compose.yml 中 LANGSERVE_GRAPHS 的 key
        all_passed = True
        
        # 步骤 1: 创建助手（关联到图）
        self.print_info("\n步骤 1: 创建助手（关联到图）...")
        assistant_id = None
        try:
            response = self.session.post(
                f"{self.base_url}/assistants",
                json={
                    "graph_id": graph_id,
                    "metadata": {}
                },
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                assistant_data = response.json()
                assistant_id = assistant_data.get("assistant_id")
                if assistant_id:
                    self.print_success(f"✅ 助手创建成功，assistant_id: {assistant_id}")
                else:
                    self.print_error("❌ 未获取到 assistant_id")
                    self.print_info(f"响应: {response.text[:200]}")
                    all_passed = False
            else:
                self.print_error(f"❌ 创建助手失败，状态码: {response.status_code}")
                self.print_info(f"响应: {response.text[:300]}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            self.print_error("❌ 创建助手请求超时")
            all_passed = False
        except Exception as e:
            self.print_error(f"❌ 创建助手失败: {str(e)}")
            all_passed = False
        
        if not assistant_id:
            self.print_info("\n⚠️  无法继续测试，因为助手创建失败")
            return False
        
        # 步骤 2: 创建线程
        self.print_info("\n步骤 2: 创建线程...")
        thread_id = None
        try:
            response = self.session.post(
                f"{self.base_url}/threads",
                json={},
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                thread_data = response.json()
                thread_id = thread_data.get("thread_id")
                if thread_id:
                    self.print_success(f"✅ 线程创建成功，thread_id: {thread_id}")
                else:
                    self.print_error("❌ 未获取到 thread_id")
                    all_passed = False
            else:
                self.print_error(f"❌ 创建线程失败，状态码: {response.status_code}")
                self.print_info(f"响应: {response.text[:200]}")
                all_passed = False
                
        except Exception as e:
            self.print_error(f"❌ 创建线程失败: {str(e)}")
            all_passed = False
        
        if not thread_id:
            self.print_info("\n⚠️  无法继续测试，因为线程创建失败")
            return False
        
        # 步骤 3: 运行图（流式）
        self.print_info("\n步骤 3: 运行图（流式）...")
        print("="*60)
        print("智能体回答:")
        print("="*60)
        try:
            response = self.session.post(
                f"{self.base_url}/threads/{thread_id}/runs/stream",
                json={
                    "assistant_id": assistant_id,
                    "input": {
                        "messages": [
                            {"role": "user", "content": "你好"}
                        ]
                    },
                    "stream_mode": "values"  # 使用 values 模式，更简洁
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                event_count = 0
                has_data = False
                final_answer = ""
                
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data:"):
                            event_count += 1
                            has_data = True
                            data_str = decoded[5:].strip()
                            try:
                                data = json.loads(data_str)
                                
                                # 提取助手消息内容
                                messages = data.get("messages", [])
                                if isinstance(messages, list) and messages:
                                    # 从后往前查找助手消息
                                    for msg in reversed(messages):
                                        content = None
                                        
                                        # 处理字典格式的消息
                                        if isinstance(msg, dict):
                                            role = msg.get("role") or msg.get("type", "")
                                            if role in ["assistant", "ai", "AIMessage"]:
                                                content = msg.get("content", "")
                                        
                                        # 如果找到内容且是新内容，打印
                                        if content and content != final_answer and len(str(content).strip()) > 0:
                                            final_answer = content
                                            print(content)
                                            break
                                
                                # 如果没有从 messages 中找到，尝试从其他字段
                                if not final_answer:
                                    # 尝试从 output 字段获取
                                    output = data.get("output", {})
                                    if isinstance(output, dict):
                                        output_messages = output.get("messages", [])
                                        if output_messages:
                                            last_msg = output_messages[-1]
                                            if isinstance(last_msg, dict):
                                                content = last_msg.get("content", "")
                                                if content and content != final_answer:
                                                    final_answer = content
                                                    print(content)
                                
                                # 调试：如果前2个事件，打印数据结构（可选）
                                if event_count <= 2:
                                    # 只在没有找到内容时打印数据结构
                                    if not final_answer:
                                        self.print_info(f"[调试] 事件 {event_count} 数据结构: {json.dumps(data, ensure_ascii=False)[:200]}...")
                                
                            except json.JSONDecodeError:
                                if event_count <= 2:
                                    self.print_info(f"事件 {event_count}: (非JSON数据) {data_str[:200]}...")
                            except Exception as e:
                                if event_count <= 2:
                                    self.print_info(f"事件 {event_count} 解析错误: {str(e)}")
                
                print("="*60)
                if final_answer:
                    self.print_success(f"✅ 流式运行成功，收到 {event_count} 个事件，已提取回答")
                elif has_data:
                    self.print_info(f"⚠️  收到 {event_count} 个事件，但未找到助手回答内容")
                    self.print_info("提示: 尝试使用 stream_mode='events' 查看详细过程")
                else:
                    self.print_info("⚠️  收到响应但无数据事件")
            else:
                self.print_error(f"❌ 流式运行失败，状态码: {response.status_code}")
                self.print_info(f"响应: {response.text[:300]}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            self.print_error("❌ 流式运行请求超时")
            all_passed = False
        except Exception as e:
            self.print_error(f"❌ 流式运行失败: {str(e)}")
            all_passed = False
        
        return all_passed
    
    def test_threads_api(self) -> bool:
        """
        测试 LangGraph API 的线程管理端点
        
        Returns:
            bool: 端点是否可用
        """
        self.print_header("3. 线程管理 API 测试")
        
        try:
            # 首先创建助手（如果还没有）
            self.print_info("创建助手（如果还没有）...")
            assistant_id = None
            try:
                response = self.session.post(
                    f"{self.base_url}/assistants",
                    json={
                        "graph_id": "agent",
                        "metadata": {}
                    },
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    assistant_data = response.json()
                    assistant_id = assistant_data.get("assistant_id")
                    if assistant_id:
                        self.print_success(f"助手创建成功，assistant_id: {assistant_id}")
                    else:
                        # 尝试获取现有助手列表
                        self.print_info("尝试获取现有助手列表...")
                        list_response = self.session.get(f"{self.base_url}/assistants", timeout=5)
                        if list_response.status_code == 200:
                            assistants = list_response.json()
                            assistant_list = assistants.get("data", [])
                            if assistant_list:
                                assistant_id = assistant_list[0].get("assistant_id")
                                self.print_info(f"使用现有助手，assistant_id: {assistant_id}")
                            else:
                                self.print_error("未找到可用的助手")
                                return False
                else:
                    # 尝试获取现有助手
                    self.print_info("创建助手失败，尝试获取现有助手...")
                    list_response = self.session.get(f"{self.base_url}/assistants", timeout=5)
                    if list_response.status_code == 200:
                        assistants = list_response.json()
                        assistant_list = assistants.get("data", [])
                        if assistant_list:
                            assistant_id = assistant_list[0].get("assistant_id")
                            self.print_info(f"使用现有助手，assistant_id: {assistant_id}")
            except Exception as e:
                self.print_info(f"助手处理异常: {str(e)}")
            
            if not assistant_id:
                self.print_error("无法获取或创建助手")
                return False
            
            # 创建线程
            self.print_info("\n创建新线程...")
            response = self.session.post(
                f"{self.base_url}/threads",
                json={},
                timeout=5
            )
            
            if response.status_code not in [200, 201]:
                self.print_error(f"创建线程失败，状态码: {response.status_code}")
                self.print_info(f"响应: {response.text[:200]}")
                return False
            
            thread_data = response.json()
            thread_id = thread_data.get("thread_id")
            
            if not thread_id:
                self.print_error("未获取到 thread_id")
                return False
            
            self.print_success(f"线程创建成功，thread_id: {thread_id}")
            
            # 测试运行流式请求
            self.print_info("\n测试流式运行...")
            run_response = self.session.post(
                f"{self.base_url}/threads/{thread_id}/runs/stream",
                json={
                    "assistant_id": assistant_id,
                    "input": {
                        "messages": [
                            {"role": "user", "content": "你好，请简单介绍一下你自己"}
                        ]
                    },
                    "stream_mode": "values"
                },
                stream=True,
                timeout=self.timeout
            )
            
            if run_response.status_code == 200:
                event_count = 0
                final_answer = ""
                print("\n" + "="*60)
                print("智能体回答:")
                print("="*60)
                
                for line in run_response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data:"):
                            event_count += 1
                            data_str = decoded[5:].strip()
                            try:
                                data = json.loads(data_str)
                                
                                # 提取助手消息内容
                                messages = data.get("messages", [])
                                if isinstance(messages, list) and messages:
                                    # 从后往前查找助手消息
                                    for msg in reversed(messages):
                                        content = None
                                        
                                        # 处理字典格式的消息
                                        if isinstance(msg, dict):
                                            role = msg.get("role") or msg.get("type", "")
                                            if role in ["assistant", "ai", "AIMessage"]:
                                                content = msg.get("content", "")
                                        
                                        # 如果找到内容且是新内容，打印
                                        if content and content != final_answer and len(str(content).strip()) > 0:
                                            final_answer = content
                                            print(content)
                                            break
                                
                                # 如果没有从 messages 中找到，尝试从其他字段
                                if not final_answer:
                                    output = data.get("output", {})
                                    if isinstance(output, dict):
                                        output_messages = output.get("messages", [])
                                        if output_messages:
                                            last_msg = output_messages[-1]
                                            if isinstance(last_msg, dict):
                                                content = last_msg.get("content", "")
                                                if content and content != final_answer:
                                                    final_answer = content
                                                    print(content)
                                
                            except:
                                pass
                
                print("="*60)
                if final_answer:
                    self.print_success(f"流式运行成功，收到 {event_count} 个事件，已提取回答")
                else:
                    self.print_info(f"流式运行成功，收到 {event_count} 个事件，但未找到回答内容")
                return True
            else:
                self.print_error(f"流式运行失败，状态码: {run_response.status_code}")
                self.print_info(f"响应: {run_response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_error(f"线程 API 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_custom_endpoints(self) -> bool:
        """
        测试自定义 API 端点（如果有）
        
        Returns:
            bool: 端点是否可用
        """
        self.print_header("4. 自定义端点测试")
        
        custom_endpoints = [
            "/chat",
            "/api/health",
            "/api/status",
        ]
        
        all_passed = True
        
        for endpoint in custom_endpoints:
            full_url = f"{self.base_url}{endpoint}"
            self.print_info(f"测试端点: {endpoint}")
            
            try:
                # 尝试 GET 请求
                response = self.session.get(full_url, timeout=5)
                
                if response.status_code == 200:
                    self.print_success(f"{endpoint} 端点存在 (GET)")
                elif response.status_code == 405:  # Method Not Allowed，说明端点存在但方法不对
                    # 尝试 POST
                    try:
                        post_response = self.session.post(
                            full_url,
                            json={"content": "test"},
                            timeout=5
                        )
                        if post_response.status_code in [200, 400]:  # 400 也算端点存在
                            self.print_success(f"{endpoint} 端点存在 (POST)")
                        else:
                            self.print_info(f"{endpoint} 端点不存在或不可用")
                    except:
                        self.print_info(f"{endpoint} 端点不存在或不可用")
                elif response.status_code == 404:
                    self.print_info(f"{endpoint} 端点不存在（这是正常的，如果未定义自定义端点）")
                else:
                    self.print_info(f"{endpoint} 返回状态码: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                self.print_error(f"无法连接到 {endpoint}")
                all_passed = False
            except Exception as e:
                self.print_info(f"{endpoint} 测试异常: {str(e)}")
        
        return all_passed
    
    def test_error_handling(self) -> bool:
        """
        测试错误处理
        
        Returns:
            bool: 错误处理是否正常
        """
        self.print_header("5. 错误处理测试")
        
        try:
            # 测试无效的图名称
            self.print_info("测试无效图名称...")
            response = self.session.post(
                f"{self.base_url}/graphs/invalid_graph/invoke",
                json={"input": {"messages": [{"role": "user", "content": "test"}]}},
                timeout=5
            )
            
            if response.status_code in [404, 400, 422]:
                self.print_success(f"错误处理正常，返回状态码: {response.status_code}")
            else:
                self.print_info(f"返回状态码: {response.status_code}")
            
            # 测试无效的输入格式
            self.print_info("测试无效输入格式...")
            response = self.session.post(
                f"{self.base_url}/graphs/agent/invoke",
                json={"invalid": "input"},
                timeout=5
            )
            
            if response.status_code in [400, 422]:
                self.print_success(f"输入验证正常，返回状态码: {response.status_code}")
            else:
                self.print_info(f"返回状态码: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.print_error(f"错误处理测试失败: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        运行所有测试
        
        Returns:
            Dict[str, bool]: 测试结果字典
        """
        print("\n" + "="*60)
        print("  Docker Compose 服务测试套件")
        print(f"  目标服务: {self.base_url}")
        print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        results = {
            "health": self.test_service_health(),
            "graph_endpoints": self.test_graph_endpoints(),
            "threads_api": self.test_threads_api(),
            "custom_endpoints": self.test_custom_endpoints(),
            "error_handling": self.test_error_handling(),
        }
        
        # 打印总结
        self.print_header("测试总结")
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name:20s}: {status}")
        
        print(f"\n总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败")
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 docker-compose 启动的 LangGraph API 服务")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:18100",
        help="服务基础 URL (默认: http://localhost:18100)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="请求超时时间（秒）(默认: 30)"
    )
    
    args = parser.parse_args()
    
    tester = DockerComposeServiceTester(base_url=args.url, timeout=args.timeout)
    results = tester.run_all_tests()
    
    # 根据测试结果设置退出码
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()

