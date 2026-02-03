
import React, { useRef, useEffect } from "react";

// 自动滚动组件
const AutoScrollDiv = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ className, children, ...props }, ref) => {
        const divRef = useRef<HTMLDivElement>(null);

        useEffect(() => {
            const element = divRef.current;
            if (!element) return;

            const scrollInterval = setInterval(() => {
                if (element.scrollHeight > element.clientHeight) {
                    element.scrollTop = element.scrollHeight;
                }
            }, 100);

            return () => clearInterval(scrollInterval);
        }, []);

        return (
            <div
                ref={(el) => {
                    // 合并refs
                    if (typeof ref === 'function') {
                        ref(el);
                    } else if (ref) {
                        ref.current = el;
                    }
                    divRef.current = el;
                }}
                className={className}
                {...props}
            >
                {children}
            </div>
        );
    }
);
AutoScrollDiv.displayName = 'AutoScrollDiv';

export { AutoScrollDiv };