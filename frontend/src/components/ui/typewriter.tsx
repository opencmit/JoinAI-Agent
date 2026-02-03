import React, { useState, useEffect } from 'react';

interface TypewriterProps {
    text: string;
    speed?: number; // 打字速度（毫秒/字符）
    className?: string;
}

export const Typewriter: React.FC<TypewriterProps> = ({
    text,
    speed = 100,
    className = ""
}) => {
    const [displayedText, setDisplayedText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        // 重置状态
        setDisplayedText('');
        setCurrentIndex(0);
    }, [text]);

    useEffect(() => {
        if (currentIndex < text.length) {
            const timer = setTimeout(() => {
                setDisplayedText(prev => prev + text[currentIndex]);
                setCurrentIndex(prev => prev + 1);
            }, speed);

            return () => clearTimeout(timer);
        }
    }, [currentIndex, text, speed]);

    // 渲染带有透明度效果的字符
    const renderTextWithOpacity = () => {
        const chars = displayedText.split('');
        return chars.map((char, index) => {
            const distanceFromEnd = chars.length - index;
            let opacity = 1; // 默认100%透明度

            // 只有在打字动画进行中时才应用透明度效果
            if (currentIndex < text.length) {
                // 根据距离末尾的位置设置透明度
                if (distanceFromEnd === 1) {
                    opacity = 0.2; // 最后一个字符 20%
                } else if (distanceFromEnd === 2) {
                    opacity = 0.5; // 倒数第二个字符 50%
                } else if (distanceFromEnd === 3) {
                    opacity = 0.8; // 倒数第三个字符 80%
                } else if (distanceFromEnd === 4) {
                    opacity = 1; // 倒数第四个字符 100%
                }
                // 距离末尾超过4个字符的保持100%透明度
            }
            // 如果打字动画结束，所有字符都保持100%透明度

            return (
                <span
                    key={index}
                    style={{ opacity }}
                    className="text-xs transition-opacity duration-150"
                >
                    {char}
                </span>
            );
        });
    };

    return (
        <span className={className}>
            {renderTextWithOpacity()}
            {/* {currentIndex < text.length && (
                <span className="animate-pulse">|</span>
            )} */}
        </span>
    );
};
