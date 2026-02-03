import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: '聚智工坊 - 管理员',
    description: '供管理员使用',
}

export default async function AdminRootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="h-screen w-full bg-[url(/chat-background.png)] bg-no-repeat bg-center bg-cover">
            {children}
        </div>
    )
}
