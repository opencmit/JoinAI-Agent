// 动画模块导出
export * from './variants';

// 常用动画配置
export const defaultTransition = {
    duration: 0.3,
    ease: "easeOut"
};

export const fastTransition = {
    duration: 0.2,
    ease: "easeOut"
};

export const slowTransition = {
    duration: 0.5,
    ease: "easeOut"
};

export const springTransition = {
    type: "spring" as const,
    stiffness: 300,
    damping: 30
};

export const bounceTransition = {
    type: "spring" as const,
    stiffness: 400,
    damping: 20
}; 