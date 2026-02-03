This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## 目录结构

langgraph_frontend
├─ public/                     # 静态资源（图片、字体等）
│   └── images/
│       └── logo.png
├── src/                       # 源码目录
│   ├── app/                   # 应用路由（App Router）
│   │   ├── api/               # API 路由
│   │   │   └── copilotkit/    
│   │   │       └── route.ts   # API 路由地址：/api/copilotkit
│   │   ├── (auth)/            # 路由组（auth）
│   │   │   └── login/         # 子路由 /login
│   │   │       └── page.tsx   # 登录页
│   │   ├── mcp-settings/      # 路由段（mcp-settings）
│   │   │   └── page.tsx       # 子路由 /mcp-settings
│   │   ├── globals.css        # 全局样式
│   │   ├── layout.tsx         # 嵌套布局
│   │   ├── page.tsx           # 主页面 /
│   │   └── favicon.ico        # 网站图标
│   ├── components/            # 公共组件
│   ├── hooks/                 # 钩子
│   ├── lib/                   # 工具函数/第三方库封装
│   └── types/                 # 全局类型定义
├── middleware.ts              # 全局中间件（必须放在根目录）
├── next.config.js             # Next.js 配置
├── package.json
└── tsconfig.json              # TypeScript 配置

## 组件列表

- 前端框架：React
- React框架：[Next.js](https://nextjs.org/)
- [CopilotKit](https://www.copilotkit.ai/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangGraph Platform](https://docs.langchain.com/langgraph-platform)
- UI框架：[Radix Primitives](https://www.radix-ui.com/primitives)
- CSS框架：
  - [tailwindcss](https://tailwindcss.com/)
  - [Tdesign](https://tdesign.tencent.com/)
- Icon库：[Lucide](https://lucide.dev/icons/)

## 初始化

```shell
# 删除已存在的store
curl -X DELETE \
-H 'Content-Type:application/json' \
'http://127.0.0.1:8000/store/items' \
-d '{"namespace": ["system"], "key": "model"}'

# 增加用于固定模型的store
curl -X PUT \
-H 'Content-Type:application/json' \
'http://127.0.0.1:8000/store/items' \
-d '{"namespace": ["system"], "key": "model", "value": {"model_name": "Qwen3-235B_sort1","model_key": "sk-kHbOKdruxXNB-thalIR0SA"}}'
```