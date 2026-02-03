"use client";

import "@assistant-ui/react-markdown/styles/dot.css";

import {
  type CodeHeaderProps,
  MarkdownTextPrimitive,
  unstable_memoizeMarkdownComponents as memoizeMarkdownComponents,
  useIsMarkdownCodeBlock,
} from "@assistant-ui/react-markdown";
import { TextContentPartProvider } from "@assistant-ui/react";
import remarkGfm from "remark-gfm";
import { type FC, memo, useState } from "react";
import { CheckIcon, CopyIcon } from "lucide-react";

import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { cn } from "@/lib/utils";
// import { SyntaxHighlighter } from "./shiki-highlighter";

interface MarkdownTextProps {
  children?: string;
  className?: string;
}

const MarkdownTextImpl = ({ children, className }: MarkdownTextProps) => {
  // 如果没有传入children，则使用原来的方式（从context获取）
  if (!children) {
    return (
      <MarkdownTextPrimitive
        remarkPlugins={[remarkGfm]}
        className={cn(
          "aui-md w-full",
          className
        )}
        components={defaultComponents}
      // componentsByLanguage={{
      //   mermaid: {
      //     SyntaxHighlighter: MermaidDiagram
      //   },
      // }}
      />
    );
  }

  // 如果传入了children，则使用TextContentPartProvider包装
  return (
    <TextContentPartProvider text={children}>
      <MarkdownTextPrimitive
        remarkPlugins={[remarkGfm]}
        className={cn(
          "aui-md w-full",
          className
        )}
        components={defaultComponents}
      // componentsByLanguage={{
      //   mermaid: {
      //     SyntaxHighlighter: MermaidDiagram
      //   },
      // }}
      />
    </TextContentPartProvider>
  );
};

export const MarkdownText = memo(MarkdownTextImpl);

const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard();
  const onCopy = () => {
    if (!code || isCopied) return;
    copyToClipboard(code);
  };

  return (
    <div className="flex items-center justify-between gap-4 rounded-t-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white">
      <span className="lowercase [&>span]:text-xs">{language}</span>
      <TooltipIconButton tooltip="Copy" onClick={onCopy}>
        {!isCopied && <CopyIcon />}
        {isCopied && <CheckIcon />}
      </TooltipIconButton>
    </div>
  );
};

const useCopyToClipboard = ({
  copiedDuration = 3000,
}: {
  copiedDuration?: number;
} = {}) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const copyToClipboard = (value: string) => {
    if (!value) return;

    // 检查 Clipboard API 是否可用
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).then(() => {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), copiedDuration);
      }).catch((err) => {
        console.error('复制失败:', err);
      });
    } else {
      // 降级方案：使用传统的 execCommand 方法
      try {
        const textArea = document.createElement('textarea');
        textArea.value = value;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (successful) {
          setIsCopied(true);
          setTimeout(() => setIsCopied(false), copiedDuration);
        } else {
          console.error('复制失败');
        }
      } catch (err) {
        console.error('复制失败:', err);
      }
    }
  };

  return { isCopied, copyToClipboard };
};

const defaultComponents = memoizeMarkdownComponents({
  // SyntaxHighlighter: SyntaxHighlighter,
  h1: ({ className, ...props }) => (
    <h1 className={cn("font-[PingFang_SC] mb-8 scroll-m-20 text-lg font-bold tracking-tight last:mb-0", className)} {...props} />
  ),
  h2: ({ className, ...props }) => (
    <h2 className={cn("font-[PingFang_SC] mb-4 mt-8 scroll-m-20 text-lg font-semibold tracking-tight first:mt-0 last:mb-0", className)} {...props} />
  ),
  h3: ({ className, ...props }) => (
    <h3 className={cn("font-[PingFang_SC] mb-4 mt-6 scroll-m-20 text-lg font-semibold tracking-tight first:mt-0 last:mb-0", className)} {...props} />
  ),
  h4: ({ className, ...props }) => (
    <h4 className={cn("font-[PingFang_SC] mb-4 mt-6 scroll-m-20 text-base tracking-tight first:mt-0 last:mb-0", className)} {...props} />
  ),
  h5: ({ className, ...props }) => (
    <h5 className={cn("font-[PingFang_SC] my-4 text-base first:mt-0 last:mb-0", className)} {...props} />
  ),
  h6: ({ className, ...props }) => (
    <h6 className={cn("font-[PingFang_SC] my-4 text-base font-medium first:mt-0 last:mb-0", className)} {...props} />
  ),
  p: ({ className, ...props }) => (
    <p className={cn("font-[PingFang_SC] mb-5 mt-5 leading-7 first:mt-0 last:mb-0", className)} {...props} />
  ),
  a: ({ className, ...props }) => (
    <a className={cn("font-[PingFang_SC] text-primary font-medium underline underline-offset-4", className)} {...props} />
  ),
  blockquote: ({ className, ...props }) => (
    <blockquote className={cn("font-[PingFang_SC] border-l-2 pl-6 italic", className)} {...props} />
  ),
  ul: ({ className, ...props }) => (
    <ul className={cn("font-[PingFang_SC] my-5 ml-6 list-disc [&>li]:mt-2", className)} {...props} />
  ),
  ol: ({ className, ...props }) => (
    <ol className={cn("font-[PingFang_SC] my-5 ml-6 list-decimal [&>li]:mt-2", className)} {...props} />
  ),
  hr: ({ className, ...props }) => (
    <hr className={cn("font-[PingFang_SC] my-5 border-b", className)} {...props} />
  ),
  table: ({ className, ...props }) => (
    <div className="w-full overflow-x-auto">
      <table className={cn("font-[PingFang_SC] my-5 w-full border-separate border-spacing-0", className)} {...props} />
    </div>
  ),
  th: ({ className, ...props }) => (
    <th className={cn("font-[PingFang_SC] bg-muted px-4 py-2 text-left font-bold first:rounded-tl-lg last:rounded-tr-lg [&[align=center]]:text-center [&[align=right]]:text-right", className)} {...props} />
  ),
  td: ({ className, ...props }) => (
    <td className={cn("font-[PingFang_SC] border-b border-l px-4 py-2 text-left last:border-r [&[align=center]]:text-center [&[align=right]]:text-right", className)} {...props} />
  ),
  tr: ({ className, ...props }) => (
    <tr className={cn("font-[PingFang_SC] m-0 border-b p-0 first:border-t [&:last-child>td:first-child]:rounded-bl-lg [&:last-child>td:last-child]:rounded-br-lg", className)} {...props} />
  ),
  sup: ({ className, ...props }) => (
    <sup className={cn("font-[PingFang_SC] [&>a]:text-xs [&>a]:no-underline", className)} {...props} />
  ),
  pre: ({ className, ...props }) => (
    <pre className={cn("font-[PingFang_SC] w-full h-full max-h-150 overflow-x-auto rounded-b-lg bg-black p-4 text-white", className)} {...props} />
  ),
  code: function Code({ className, ...props }) {
    const isCodeBlock = useIsMarkdownCodeBlock();
    return (
      <code
        className={cn(!isCodeBlock && "font-[PingFang_SC] bg-muted rounded border font-semibold", className)}
        {...props}
      />
    );
  },
  CodeHeader,
});
