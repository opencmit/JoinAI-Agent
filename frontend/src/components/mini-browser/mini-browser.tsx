"use client";

import React, { useState, useRef } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw, Globe, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MiniBrowserProps {
  /** 初始网址 */
  url: string;
  /** 是否禁用用户在 UI 中自定义输入网址 */
  disableUrlInput?: boolean;
  /** 组件的额外 CSS 类名 */
  className?: string;
  /** iframe 的高度 */
  height?: string | number;
  /** 网址变化时的回调函数 */
  onUrlChange?: (url: string) => void;
  /** 刷新时的回调函数 */
  onRefresh?: () => void;
}

export function MiniBrowser({
  url,
  disableUrlInput = false,
  className,
  height = "400px",
  onUrlChange,
  onRefresh,
}: MiniBrowserProps) {
  const [currentUrl, setCurrentUrl] = useState(url);
  const [inputUrl, setInputUrl] = useState(url);
  const [isLoading, setIsLoading] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // 处理网址导航
  const handleNavigate = () => {
    if (!inputUrl.trim()) return;
    
    let formattedUrl = inputUrl.trim();
    // 如果没有协议，默认添加 https://
    if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
      formattedUrl = `https://${formattedUrl}`;
    }
    
    setCurrentUrl(formattedUrl);
    setInputUrl(formattedUrl);
    onUrlChange?.(formattedUrl);
  };

  // 处理刷新
  const handleRefresh = () => {
    setIsLoading(true);
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
    }
    onRefresh?.();
    // 模拟加载时间
    setTimeout(() => setIsLoading(false), 1000);
  };

  // 处理回车键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNavigate();
    }
  };

  // iframe 加载完成
  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  // iframe 开始加载
  const handleIframeLoadStart = () => {
    setIsLoading(true);
  };

  return (
    <Card className={cn("w-full gap-1 pt-3 pb-0", className)}>
      <CardHeader className="pb-0">
        <div className="flex items-center gap-1">
          {/* 地址栏图标 */}
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-muted">
            {disableUrlInput ? (
              <Lock className="w-4 h-4 text-muted-foreground" />
            ) : (
              <Globe className="w-4 h-4 text-muted-foreground" />
            )}
          </div>
          
          {/* 地址栏输入框 */}
          <div className="flex-1">
            <Input
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入网址..."
              readOnly={disableUrlInput}
              className={cn(
                "font-mono text-sm",
                disableUrlInput && "cursor-not-allowed"
              )}
            />
          </div>
          
          {/* 导航按钮 - 只在允许输入时显示 */}
          {!disableUrlInput && (
            <Button
              onClick={handleNavigate}
              variant="outline"
              size="sm"
              disabled={!inputUrl.trim() || inputUrl === currentUrl}
            >
              前往
            </Button>
          )}
          
          {/* 刷新按钮 */}
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            disabled={isLoading}
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="relative">
          {/* 加载指示器 */}
          {isLoading && (
            <div className="absolute top-0 left-0 right-0 h-1 bg-muted overflow-hidden z-10">
              <div className="h-full bg-primary animate-pulse" />
            </div>
          )}
          
          {/* iframe 容器 */}
          <div 
            className="w-full border-t overflow-hidden rounded-b-xl"
            style={{ height }}
          >
            <iframe
              ref={iframeRef}
              src={currentUrl}
              className="w-full h-full border-0"
              onLoad={handleIframeLoad}
              onLoadStart={handleIframeLoadStart}
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
              title="Mini Browser"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default MiniBrowser; 