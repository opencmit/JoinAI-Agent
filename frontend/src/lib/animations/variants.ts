// Motion动画变体定义
import { Variants } from "motion/react";

// 页面切换动画变体
export const pageVariants: Variants = {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.05 }
};

// 卡片动画变体
export const cardVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    },
    hover: {
        scale: 1.02,
        y: -2,
        transition: { duration: 0.2, ease: "easeOut" }
    }
};

// 输入框动画变体
export const inputVariants: Variants = {
    idle: { scale: 1, borderColor: "rgb(229, 231, 235)" },
    focused: {
        scale: 1.01,
        borderColor: "rgb(59, 130, 246)",
        transition: { duration: 0.2 }
    }
};

// 按钮动画变体
export const buttonVariants: Variants = {
    idle: { scale: 1 },
    hover: { scale: 1.05 },
    tap: { scale: 0.95 }
};

// 徽章/标签动画变体
export const badgeVariants: Variants = {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 }
};

// 列表项渐入动画变体
export const listItemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    }
};

// 模态框/弹窗动画变体
export const modalVariants: Variants = {
    hidden: { opacity: 0, scale: 0.95, y: 20 },
    visible: {
        opacity: 1,
        scale: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    },
    exit: {
        opacity: 0,
        scale: 0.95,
        y: 20,
        transition: { duration: 0.2, ease: "easeIn" }
    }
};

// 侧边栏动画变体
export const sidebarVariants: Variants = {
    hidden: { opacity: 0, x: 100, width: 0 },
    visible: {
        opacity: 1,
        x: 0,
        width: '50%',
        transition: { duration: 0.3, ease: "easeOut" }
    },
    sandbox: {
        opacity: 1,
        x: 0,
        width: '66.666667%',
        transition: { duration: 0.3, ease: "easeOut" }
    },
    exit: {
        opacity: 0,
        x: 100,
        width: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    }
};

// 淡入淡出动画变体
export const fadeVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 }
};

// 从下方滑入动画变体
export const slideUpVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    },
    exit: {
        opacity: 0,
        y: -20,
        transition: { duration: 0.2, ease: "easeIn" }
    }
};

// 从上方滑入动画变体
export const slideDownVariants: Variants = {
    hidden: { opacity: 0, y: -20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    },
    exit: {
        opacity: 0,
        y: -20,
        transition: { duration: 0.2, ease: "easeIn" }
    }
};

// 旋转缩放动画变体（适用于Logo等）
export const logoVariants: Variants = {
    initial: { scale: 0, rotate: -180 },
    animate: {
        scale: 1,
        rotate: 0,
        transition: { duration: 0.6, delay: 0.3, type: "spring", stiffness: 200 }
    },
    hover: { scale: 1.1, rotate: 5 }
};

// 分组动画变体（用于容器）
export const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2
        }
    }
};

// 弹性动画变体
export const bounceVariants: Variants = {
    initial: { scale: 0.8, opacity: 0 },
    animate: {
        scale: 1,
        opacity: 1,
        transition: {
            type: "spring",
            stiffness: 300,
            damping: 20
        }
    }
};

// 打字机效果动画变体（闪烁光标）
export const typingDotsVariants: Variants = {
    animate: {
        opacity: [1, 0, 1],
        transition: {
            duration: 1.2,
            repeat: Infinity,
            ease: "easeInOut"
        }
    }
}; 