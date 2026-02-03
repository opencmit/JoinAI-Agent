import requests
import json
import sys


BASE_URL = "http://localhost:18100"
ASSISTANT_ID = "agent" 

def debug_agent():
    print(f"🔍 连接服务: {BASE_URL}")
    
    # 1. 建线程
    try:
        thread = requests.post(f"{BASE_URL}/threads", json={}).json()
        thread_id = thread["thread_id"]
        print(f"✅ 线程 ID: {thread_id}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 2. 发送请求
    question = "2024年欧洲杯冠军是谁？"
    print(f"🚀 发送问题: {question}\n")
    
    run_url = f"{BASE_URL}/threads/{thread_id}/runs/stream"
    
    try:
        # 使用 'events' 模式，因为它是最详细的，包含所有步骤和错误信息
        with requests.post(
            run_url,
            json={
                "assistant_id": ASSISTANT_ID,
                "input": {"messages": [{"role": "user", "content": question}]},
                "stream_mode": "events"  # <--- 改回 events 模式以便查错
            },
            stream=True
        ) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    
                    # 打印原始事件类型
                    if decoded_line.startswith("event:"):
                        event_type = decoded_line.split(":", 1)[1].strip()
                        print(f"\n[事件: {event_type}]")
                    
                    # 打印并解析数据
                    if decoded_line.startswith("data:"):
                        data_str = decoded_line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            
                            # --- 核心：尝试提取有用信息并高亮显示 ---
                            
                            # 1. 检查是否有错误
                            if "error" in data:
                                print(f"❌ 发生错误: {data['error']}")
                                print(f"   详情: {data.get('message', '')}")
                            
                            # 2. 检查是否有 AI 回复 (on_chat_model_stream)
                            elif data.get("event") == "on_chat_model_stream":
                                chunk = data.get("data", {}).get("chunk", {})
                                content = chunk.get("content", "")
                                if content:
                                    # 实时打印出 AI 的字（不换行）
                                    print(content, end="", flush=True)
                                    
                            # 3. 检查是否有工具调用
                            elif data.get("event") == "on_tool_start":
                                tool_name = data.get("name", "Unknown Tool")
                                tool_input = data.get("data", {}).get("input")
                                print(f"\n🛠️ 调用工具: {tool_name}")
                                print(f"   参数: {tool_input}")

                            # 4. 其他数据直接打印摘要，防止刷屏
                            else:
                                # 如果想看完整数据，取消下面这行的注释
                                # print(json.dumps(data, indent=2, ensure_ascii=False))
                                pass

                        except:
                            print(f"   (原始数据): {data_str}")

            print("\n\n✅ 结束。")

    except Exception as e:
        print(f"\n❌ 请求中断: {e}")

if __name__ == "__main__":
    debug_agent()