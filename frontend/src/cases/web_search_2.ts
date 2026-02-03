export const web_search_2 = [
    {
        "type": "config",
        "state": {
            "agent_type": "normal"
        }
    },
    {
        "type": "message-user",
        "content": {
            "id": "ck-7ed7c155-dab3-4faf-95b5-e769c9691831",
            "role": "user",
            "content": "搜索一下北京5天的天气"
        }
    },
    {
        "type": "message-web",
        "content": {
            "id": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
            "role": "assistant",
            "toolCalls": [
                {
                    "id": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
                    "function": {
                        "name": "web",
                        "arguments": "{\"operation\":\"search\",\"sub_queries\":[{\"query\":\"北京 未来5天 天气预报\",\"topic\":\"general\",\"days\":3}]}"
                    },
                    "type": "function"
                }
            ],
            "name": "web"
        }
    },
    {
        "type": "message-web-result",
        "content": {
            "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96": {
                "https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845#bocha": {
                    "url": "https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845",
                    "title": "2025年08月04日北京天气预报",
                    "content": "2025年08月04日北京天气预报:\n08/04 (周一):\n天气:中雨,温度:28/23°C,风向风力:东南风<3级\n08/05 (周二):\n天气:多云,温度:31/23°C,风向风力:南风<3级\n08/06 (周三):\n天气:多云转晴,温度:33/24°C,风向风力:西北风<3级\n08/07 (周四):\n天气:多云,温度:32/24°C,风向风力:西南风<3级\n08/08 (周五):\n天气:阴转雷阵雨,温度:28/22°C,风向风力:北风<3级\n08/09 (周六):\n天气:小雨,温度:29/22°C,风向风力:东风<3级\n08/10 (周日):\n天气:多云转晴,温度:30/22°C,风向",
                    "provider": "bocha",
                    "score": 0
                },
                "https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e#bocha": {
                    "url": "https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e",
                    "title": "2025年08月04日政和天气预报",
                    "content": "2025年08月04日政和天气预报:\n08/04 (周一):\n天气:小雨转多云,温度:35/24°C,风向风力:无持续风向<3级\n08/05 (周二):\n天气:小雨转多云,温度:34/23°C,风向风力:无持续风向<3级\n08/06 (周三):\n天气:小雨转多云,温度:33/23°C,风向风力:无持续风向<3级\n08/07 (周四):\n天气:多云,温度:35/24°C,风向风力:无持续风向<3级\n08/08 (周五):\n天气:多云,温度:36/24°C,风向风力:无持续风向<3级\n08/09 (周六):\n天气:多云,温度:37/25°C,风向风力:无持续风向<3级\n08/10 (周日):\n天气",
                    "provider": "bocha",
                    "score": 0
                }
            }
        }
    },
    {
        "type": "message",
        "content": {
            "id": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4",
            "role": "assistant",
            "content": "## 搜索结果分析\n\n根据搜索结果，我找到了一个可靠的天气预报网站，提供了北京未来5天的天气预报信息。以下是具体的天气情况：\n\n### 北京未来5天天气预报\n\n- **08/05 (周二)**:\n  - 天气: 多云\n  - 温度: 31/23°C\n  - 风向风力: 南风 <3级\n\n- **08/06 (周三)**:\n  - 天气: 多云转晴\n  - 温度: 33/24°C\n  - 风向风力: 西北风 <3级\n\n- **08/07 (周四)**:\n  - 天气: 多云\n  - 温度: 32/24°C\n  - 风向风力: 西南风 <3级\n\n- **08/08 (周五)**:\n  - 天气: 阴转雷阵雨\n  - 温度: 28/22°C\n  - 风向风力: 北风 <3级\n\n- **08/09 (周六)**:\n  - 天气: 小雨\n  - 温度: 29/22°C\n  - 风向风力: 东风 <3级\n\n### 数据来源\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845)\n\n如果您需要更多详细信息或有其他问题，请告诉我！"
        }
    }
]

