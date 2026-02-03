export default function Loading() {
    // Or a custom loading skeleton component
    return (
        <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600 after:content-[''] after:animate-dot-blink">加载中</p>
            </div>
        </div>
    )
}