"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export default function LoginRequiredPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <Card className="w-full max-w-md shadow-lg">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                        <AlertCircle className="h-8 w-8 text-red-600" />
                    </div>
                    <CardTitle className="text-2xl font-bold text-gray-900">
                        尚未登录或登录信息过期
                    </CardTitle>
                    {/* <CardDescription className="text-gray-600">
                        请先登录后再访问此页面
                    </CardDescription> */}
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="text-sm text-gray-500 text-center">
                        <p>系统检测到您尚未登录或登录信息已过期</p>
                    </div>

                    <div className="text-xs text-gray-400 text-center pt-4 border-t">
                        <p>如果问题持续存在，请联系系统管理员</p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
} 