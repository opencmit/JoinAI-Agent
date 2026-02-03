import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# supervisor 管理的普通智能体
TEAM_MEMBERS_INNER = ["researcher", "coder", "reporter"]

# supervisor 可以路由的智能体
TEAM_MEMBERS = TEAM_MEMBERS_INNER + ["a2a_agent", "mcp_tool"]

RESPONSE_FORMAT = "Response from {}:\n\n<response>\n{}\n</response>\n\n"

# *Please execute the next step.*