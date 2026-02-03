# Motion动画变体库

这个模块包含了项目中常用的motion动画变体，可以在任何组件中复用。

## 使用方法

```typescript
import { pageVariants, cardVariants, buttonVariants } from '@/lib/animations';
import { motion } from 'motion/react';

// 使用页面动画变体
<motion.div
  variants={pageVariants}
  initial="initial"
  animate="animate"
  exit="exit"
>
  页面内容
</motion.div>

// 使用卡片动画变体
<motion.div
  variants={cardVariants}
  initial="hidden"
  animate="visible"
  whileHover="hover"
>
  卡片内容
</motion.div>

// 使用按钮动画变体
<motion.button
  variants={buttonVariants}
  whileHover="hover"
  whileTap="tap"
>
  按钮
</motion.button>
```

## 可用的动画变体

### 页面动画
- `pageVariants`: 页面切换时的缩放淡入淡出效果
- `modalVariants`: 模态框弹出效果
- `slideUpVariants`: 从下方滑入
- `slideDownVariants`: 从上方滑入
- `fadeVariants`: 简单的淡入淡出

### 组件动画
- `cardVariants`: 卡片的悬浮和渐入效果
- `buttonVariants`: 按钮的悬浮和点击效果
- `badgeVariants`: 徽章的缩放渐入效果
- `inputVariants`: 输入框的聚焦效果

### 布局动画
- `sidebarVariants`: 侧边栏滑入滑出效果
- `containerVariants`: 容器的分组动画效果
- `listItemVariants`: 列表项的渐入效果

### 特殊动画
- `logoVariants`: Logo的旋转缩放效果
- `bounceVariants`: 弹性效果

## 常用动画配置

还提供了一些预定义的过渡配置：

```typescript
import { defaultTransition, fastTransition, springTransition } from '@/lib/animations';

// 使用预定义的过渡配置
<motion.div
  transition={springTransition}
  animate={{ scale: 1.1 }}
>
  内容
</motion.div>
```

## 扩展动画变体

要添加新的动画变体，只需在 `variants.ts` 文件中添加：

```typescript
export const myCustomVariants: Variants = {
  initial: { opacity: 0, rotate: -90 },
  animate: { opacity: 1, rotate: 0 },
  exit: { opacity: 0, rotate: 90 }
};
```

然后在 `index.ts` 中导出：

```typescript
export * from './variants';
``` 