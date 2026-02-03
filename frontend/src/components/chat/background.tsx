// components/Background.tsx
import React from "react";

export default function Background({ style }: { style: React.CSSProperties }) {
    return (
        <div className="relative min-h-screen w-full overflow-hidden flex items-center justify-center p-6" style={style}>
            {/* 苹果风格多层渐变背景 */}
            <div
                className="absolute inset-0 -z-10"
                style={{
                    background: `
                        linear-gradient(135deg, 
                            rgba(255, 255, 255, 0.95) 0%, 
                            rgba(248, 250, 252, 0.9) 25%,
                            rgba(241, 245, 249, 0.85) 50%,
                            rgba(226, 232, 240, 0.8) 75%,
                            rgba(203, 213, 225, 0.75) 100%
                        ),
                        radial-gradient(ellipse 800px 600px at 25% 20%, 
                            rgba(59, 130, 246, 0.12) 0%, 
                            transparent 60%
                        ),
                        radial-gradient(ellipse 600px 800px at 75% 80%, 
                            rgba(168, 85, 247, 0.08) 0%, 
                            transparent 60%
                        ),
                        radial-gradient(ellipse 400px 300px at 45% 60%, 
                            rgba(14, 165, 233, 0.06) 0%, 
                            transparent 70%
                        )
                    `,
                    backgroundColor: "#fefefe",
                }}
            />

            {/* 苹果风格浮动装饰元素 */}
            <div className="absolute inset-0 -z-5 overflow-hidden">
                {/* 大圆形装饰 */}
                <div
                    className="absolute w-96 h-96 rounded-full opacity-30"
                    style={{
                        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 197, 253, 0.05))',
                        top: '-10%',
                        right: '-15%',
                        filter: 'blur(60px)',
                    }}
                />

                {/* 中等圆形装饰 */}
                <div
                    className="absolute w-64 h-64 rounded-full opacity-20"
                    style={{
                        background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(196, 181, 253, 0.05))',
                        bottom: '-5%',
                        left: '-10%',
                        filter: 'blur(40px)',
                    }}
                />

                {/* 小圆形装饰 */}
                <div
                    className="absolute w-32 h-32 rounded-full opacity-25"
                    style={{
                        background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(125, 211, 252, 0.08))',
                        top: '60%',
                        right: '20%',
                        filter: 'blur(30px)',
                    }}
                />
            </div>

            {/* 苹果风格玻璃拟态网格图案 */}
            <div
                className="absolute inset-0 -z-8 opacity-[0.02]"
                style={{
                    backgroundImage: `
                        radial-gradient(circle at 1px 1px, rgba(0,0,0,0.3) 1px, transparent 0)
                    `,
                    backgroundSize: '32px 32px',
                }}
            />
        </div>
    );
}
