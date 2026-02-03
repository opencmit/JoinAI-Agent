import "@noahlocal/copilotkit-react-ui/styles.css";
import 'tdesign-react/dist/tdesign.css';
import "./globals.css";
import "tdesign-react/es/_util/react-19-adapter";
import { UserProvider } from "@/lib/user-context";
import { ToastProvider } from "@/lib/toast";
import { SidebarProvider } from "@/components/ui/sidebar"

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME,
  icons: '/logo.png'
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className="font-[PingFang_SC]! antialiased overflow-hidden!">
        <ToastProvider>
          <UserProvider>
            <SidebarProvider>
              {children}
            </SidebarProvider>
          </UserProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
