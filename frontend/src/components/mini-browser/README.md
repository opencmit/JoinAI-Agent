# MiniBrowser 组件

一个基于 React 和 Shadcn UI 的迷你浏览器组件，支持在应用内嵌入网页浏览功能。

## 功能特性

- 🌐 **网址导航**: 支持输入网址并导航到指定页面
- 🔒 **输入控制**: 可以禁用用户自定义输入网址，只允许查看指定网址
- 🔄 **刷新功能**: 内置刷新按钮，支持重新加载页面
- 📱 **响应式设计**: 自适应不同屏幕尺寸
- 🎨 **一致的设计风格**: 与项目中其他 Shadcn UI 组件保持一致的设计风格
- ⚡ **加载指示器**: 显示页面加载状态
- 🛡️ **安全沙箱**: iframe 使用安全的沙箱属性

## 安装和导入

```tsx
import { MiniBrowser } from "@/components/mini-browser";
// 或者
import MiniBrowser from "@/components/mini-browser";
```

## 基本用法

### 允许用户输入网址

```tsx
<MiniBrowser
  url="https://www.google.com"
  height="400px"
  onUrlChange={(url) => console.log("网址变化:", url)}
  onRefresh={() => console.log("页面刷新")}
/>
```

### 禁用用户输入（只读模式）

```tsx
<MiniBrowser
  url="https://www.github.com"
  disableUrlInput={true}
  height="300px"
/>
```

## API 参考

### MiniBrowserProps

| 属性 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `url` | `string` | ✅ | - | 初始网址 |
| `disableUrlInput` | `boolean` | ❌ | `false` | 是否禁用用户在 UI 中自定义输入网址 |
| `className` | `string` | ❌ | - | 组件的额外 CSS 类名 |
| `height` | `string \| number` | ❌ | `"400px"` | iframe 的高度 |
| `onUrlChange` | `(url: string) => void` | ❌ | - | 网址变化时的回调函数 |
| `onRefresh` | `() => void` | ❌ | - | 刷新时的回调函数 |

## 使用场景

1. **文档预览**: 在应用内预览外部文档或网页
2. **内容展示**: 展示特定的网页内容，不允许用户随意导航
3. **开发工具**: 作为开发工具的一部分，用于预览和测试网页
4. **教学演示**: 在教学应用中展示特定的网页内容

## 设计特点

- 使用 Shadcn UI 的 `Card`、`Input`、`Button` 组件保持设计一致性
- 采用 Lucide React 图标库的图标
- 支持深色模式
- 响应式布局，适配不同屏幕尺寸
- 符合现代 Web 设计规范

## 注意事项

1. **跨域限制**: 某些网站可能不允许在 iframe 中加载，这是浏览器的安全限制
2. **HTTPS 要求**: 建议使用 HTTPS 网址以避免混合内容问题
3. **性能考虑**: 加载外部网页可能影响应用性能，建议合理使用
4. **安全性**: iframe 使用了安全的沙箱属性，但仍需注意加载可信的网站

## 技术实现

- 基于 React Hooks (`useState`, `useRef`) 实现状态管理
- 使用 TypeScript 提供类型安全
- 采用 Tailwind CSS 进行样式设计
- 使用 `cn` 工具函数进行类名合并
- iframe 沙箱模式确保安全性 