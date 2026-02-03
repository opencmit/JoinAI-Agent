export const mcp_tool_1 = [
    {
        "type": "config",
        "state": {
            "agent_type": "normal"
        }
    },
    {
        "type": "message-user",
        "content": {
            "id": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47",
            "role": "user",
            "content": "使用文生图工具，生成一张孩子嬉戏玩闹的图片"
        }
    },
    {
        "type": "log-new",
        "content": {
            "message": "正在思考中...",
            "done": false,
            "messageId": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47"
        }
    },
    {
        "type": "log-previous",
        "content": {
            "message": "思考完成",
            "done": true,
            "messageId": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47"
        }
    },
    {
        "type": "log-new",
        "content": {
            "message": "MCP智能体执行中",
            "done": false,
            "messageId": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47"
        }
    },
    {
        "type": "log-previous",
        "content": {
            "message": "MCP智能体执行完成",
            "done": true,
            "messageId": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47"
        }
    },
    {
        "type": "message-tool",
        "content": {
            "id": "dd6d9ec3bbdc5ebd9f9bf61f573548cf",
            "role": "assistant",
            "toolCalls": [
                {
                    "id": "chatcmpl-tool-dd6d9ec3bbdc4ebd9f9bf61f573548cf",
                    "function": {
                        "name": "文生图",
                        "arguments": "{\"input\":\"小孩嬉戏玩闹\",\"width\":\"1024\",\"height\":\"1024\",\"description\":\"\"}"
                    },
                    "type": "function"
                }
            ],
            "name": "文生图"
        }
    },
    {
        "type": "message-tool",
        "content": {
            "id": "e2e1075c-43a9-4832-a00a-1197cf82f896",
            "role": "tool",
            "content": "{\n  \"code\": \"2000\",\n  \"msg\": \"生成成功\",\n  \"data\": \"![BLSCCZAKHKYMHVXM.png](/agentV2/proxyApi/turing-planet/turing/planet/v2/file/download/TOSS_VjowMixCTjpmbGFtZXMsT046Y3pNNkx5OXdiR0Z1WlhSVWFXUXZjR3hoYm1WMEx6SXdNalV3T1RJNEwwSk1VME5EV2tGTFNFdFpUVWhXV0UwdWNHNW4=_TOSS)\"\n}",
            "toolCallId": "chatcmpl-tool-dd6d9ec3bbdc4ebd9f9bf61f573548cf",
            "toolName": "文生图"
        }
    },
    {
        "type": "message-design",
        "content": {
            "id": "run-a7116f63-244a-4a1c-8aed-f60660144456",
            "role": "assistant",
            "content": "![BLSCCZAKHKYMHVXM.png](/agentV2/proxyApi/turing-planet/turing/planet/v2/file/download/TOSS_VjowMixCTjpmbGFtZXMsT046Y3pNNkx5OXdiR0Z1WlhSVWFXUXZjR3hoYm1WMEx6SXdNalV3T1RJNEwwSk1VME5EV2tGTFNFdFpUVWhXV0UwdWNHNW4=_TOSS)"
        }
    }
]