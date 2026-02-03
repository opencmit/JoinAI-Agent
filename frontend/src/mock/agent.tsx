import { Message } from "@noahlocal/copilotkit-shared";

import { MessageStatusCode, MessageRole, TextMessage, ActionExecutionMessage, ResultMessage, AgentStateMessage } from "@noahlocal/copilotkit-runtime-client-gql";

export const test_message_1 = [
    new TextMessage({
        "id": "ck-32a70baf-71b5-4481-bed4-32dc5b6de66a",
        "role": MessageRole.User,
        "content": "写hello到文件中",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new TextMessage({
        "id": "run-e2313245-5d3a-4353-a705-22b90f250c76",
        "role": MessageRole.Assistant,
        "content": "好的，我将创建一个文件并将 \"hello\" 写入其中。以下是具体步骤：\n\n1. 使用 `files` 工具创建一个新文件。\n2. 将 \"hello\" 写入该文件。\n\n让我们开始吧。\n\n### 创建文件并写入内容\n\n首先，我将创建一个名为 `hello.txt` 的文件，并将 \"hello\" 写入其中。\n",
        "parentMessageId": "run-e2313245-5d3a-4353-a705-22b90f250c76",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-69032adac6c24d60a5151d825f62ce95",
        "name": "files",
        "arguments": {
            "operation": "write",
            "path": "hello.txt",
            "content": "hello"
        },
        "parentMessageId": "run-e2313245-5d3a-4353-a705-22b90f250c76",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "fda6c156-38b3-4d98-97cc-0eed0f339398",
        "result": "文件 'hello.txt' 完全重写成功",
        "actionExecutionId": "chatcmpl-tool-69032adac6c24d60a5151d825f62ce95",
        "actionName": "files",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-774b11c1-bf74-4728-ab11-7c85a267bac6",
        "role": MessageRole.Assistant,
        "content": "文件 `hello.txt` 已成功创建，并将 \\\"hello\\\" 写入其中。\n\n### 验证文件内容\n\n为了确保内容正确写入，我将读取文件内容并验证。\n\n接下来，我将读取 `hello.txt` 文件的内容。\n",
        "parentMessageId": "run-774b11c1-bf74-4728-ab11-7c85a267bac6",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-c9a6fa0593304a39919fee42dd7bb254",
        "name": "files",
        "arguments": {
            "operation": "read",
            "path": "hello.txt"
        },
        "parentMessageId": "run-774b11c1-bf74-4728-ab11-7c85a267bac6",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "a3c8c2af-c4f9-4597-9d4d-856a18c5d1e5",
        "result": "文件内容:\nhello",
        "actionExecutionId": "chatcmpl-tool-c9a6fa0593304a39919fee42dd7bb254",
        "actionName": "files",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-7af85044-7d2b-4a37-b7aa-6a253aa1cf27",
        "role": MessageRole.Assistant,
        "content": "文件 `hello.txt` 的内容已成功验证，内容为：\n\n```\nhello\n```\n\n任务完成！如果您需要进一步的操作，请告诉我。",
        "parentMessageId": "run-7af85044-7d2b-4a37-b7aa-6a253aa1cf27",
        "createdAt": "2025-07-16T06:22:22.025Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
];

export const text_html_1 = '\n<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>圆形绘制工具</title>\n    <script src="https://cdn.tailwindcss.com/3.3.3"></script>\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">\n    <style>\n        body {\n            font-family: \'Noto Sans SC\', sans-serif;\n            background-color: #f8fafc;\n        }\n        .glassmorphism {\n            background: rgba(255, 255, 255, 0.7);\n            backdrop-filter: blur(10px);\n            border-radius: 16px;\n            border: 1px solid rgba(255, 255, 255, 0.3);\n            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);\n        }\n        .btn-primary {\n            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);\n            color: white;\n            transition: all 0.3s ease;\n        }\n        .btn-primary:hover {\n            transform: translateY(-2px);\n            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5);\n        }\n        .btn-secondary {\n            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);\n            transition: all 0.3s ease;\n        }\n        .btn-secondary:hover {\n            transform: translateY(-2px);\n            box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.2);\n        }\n        input:focus, select:focus {\n            outline: none;\n            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3);\n        }\n    </style>\n</head>\n<body class="min-h-screen flex flex-col items-center justify-center p-4">\n    <div class="w-full max-w-4xl">\n        <h1 class="text-3xl font-bold text-center mb-8 text-gray-800">圆形绘制工具</h1>\n        \n        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">\n            <!-- 绘图区域 -->\n            <div class="glassmorphism p-6">\n                <h2 class="text-xl font-semibold mb-4 text-gray-700">绘图区域</h2>\n                <canvas id="drawingCanvas" class="w-full h-96 bg-white rounded-lg shadow-md"></canvas>\n            </div>\n            \n            <!-- 控制面板 -->\n            <div class="glassmorphism p-6">\n                <h2 class="text-xl font-semibold mb-4 text-gray-700">控制面板</h2>\n                \n                <div class="space-y-4">\n                    <!-- 半径输入 -->\n                    <div>\n                        <label for="radius" class="block text-sm font-medium text-gray-700 mb-1">圆半径 (px)</label>\n                        <input type="number" id="radius" min="1" value="50" \n                               class="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-indigo-500">\n                    </div>\n                    \n                    <!-- 颜色选择 -->\n                    <div>\n                        <label for="color" class="block text-sm font-medium text-gray-700 mb-1">圆颜色</label>\n                        <select id="color" class="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-indigo-500">\n                            <option value="#4f46e5">紫色</option>\n                            <option value="#3b82f6">蓝色</option>\n                            <option value="#10b981">绿色</option>\n                            <option value="#ef4444">红色</option>\n                            <option value="#f59e0b">黄色</option>\n                            <option value="#000000">黑色</option>\n                        </select>\n                    </div>\n                    \n                    <!-- X坐标 -->\n                    <div>\n                        <label for="xPos" class="block text-sm font-medium text-gray-700 mb-1">X坐标 (px)</label>\n                        <input type="number" id="xPos" min="0" value="200" \n                               class="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-indigo-500">\n                    </div>\n                    \n                    <!-- Y坐标 -->\n                    <div>\n                        <label for="yPos" class="block text-sm font-medium text-gray-700 mb-1">Y坐标 (px)</label>\n                        <input type="number" id="yPos" min="0" value="150" \n                               class="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-indigo-500">\n                    </div>\n                    \n                    <!-- 按钮组 -->\n                    <div class="flex space-x-4 pt-4">\n                        <button id="drawBtn" class="btn-primary px-6 py-2 rounded-lg font-medium flex-1">\n                            <i class="fas fa-draw-polygon mr-2"></i>绘制圆形\n                        </button>\n                        <button id="clearBtn" class="btn-secondary px-6 py-2 rounded-lg font-medium flex-1">\n                            <i class="fas fa-trash-alt mr-2"></i>清除画布\n                        </button>\n                    </div>\n                </div>\n            </div>\n        </div>\n    </div>\n\n    <footer class="mt-12 text-center text-gray-500 text-sm">\n        <p>created by <a href="https://space.coze.cn" class="text-indigo-600 hover:underline">coze space</a></p>\n        <p>页面内容均由 AI 生成，仅供参考</p>\n    </footer>\n\n    <script>\n        document.addEventListener(\'DOMContentLoaded\', function() {\n            const canvas = document.getElementById(\'drawingCanvas\');\n            const ctx = canvas.getContext(\'2d\');\n            \n            // 设置canvas实际尺寸\n            function resizeCanvas() {\n                const rect = canvas.getBoundingClientRect();\n                canvas.width = rect.width;\n                canvas.height = rect.height;\n                \n                // 清除并重绘\n                clearCanvas();\n            }\n            \n            // 初始化canvas尺寸\n            resizeCanvas();\n            window.addEventListener(\'resize\', resizeCanvas);\n            \n            // 清除画布\n            function clearCanvas() {\n                ctx.clearRect(0, 0, canvas.width, canvas.height);\n                ctx.fillStyle = \'#ffffff\';\n                ctx.fillRect(0, 0, canvas.width, canvas.height);\n            }\n            \n            // 绘制圆形\n            function drawCircle() {\n                const radius = parseInt(document.getElementById(\'radius\').value);\n                const color = document.getElementById(\'color\').value;\n                const xPos = parseInt(document.getElementById(\'xPos\').value);\n                const yPos = parseInt(document.getElementById(\'yPos\').value);\n                \n                ctx.beginPath();\n                ctx.arc(xPos, yPos, radius, 0, Math.PI * 2);\n                ctx.fillStyle = color;\n                ctx.fill();\n                ctx.strokeStyle = \'#000000\';\n                ctx.lineWidth = 1;\n                ctx.stroke();\n            }\n            \n            // 按钮事件\n            document.getElementById(\'drawBtn\').addEventListener(\'click\', drawCircle);\n            document.getElementById(\'clearBtn\').addEventListener(\'click\', clearCanvas);\n            \n            // 初始化画布\n            clearCanvas();\n        });\n    </script>\n</body>\n</html>'

export const test_html_2 = "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>一元一次方程交互式学习工具</title>\n    <style>\n        * {\n            box-sizing: border-box;\n            margin: 0;\n            padding: 0;\n            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n        }\n\n        body {\n            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);\n            min-height: 100vh;\n            display: flex;\n            justify-content: center;\n            align-items: center;\n            padding: 20px;\n            color: #333;\n        }\n\n        .container {\n            background-color: rgba(255, 255, 255, 0.95);\n            border-radius: 20px;\n            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);\n            width: 100%;\n            max-width: 900px;\n            overflow: hidden;\n        }\n\n        header {\n            background: linear-gradient(90deg, #ff416c, #ff4b2b);\n            color: white;\n            padding: 25px;\n            text-align: center;\n        }\n\n        h1 {\n            font-size: 2.5rem;\n            margin-bottom: 10px;\n            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);\n        }\n\n        .subtitle {\n            font-size: 1.2rem;\n            opacity: 0.9;\n        }\n\n        .content {\n            display: flex;\n            flex-wrap: wrap;\n            padding: 20px;\n        }\n\n        .equation-section {\n            flex: 1;\n            min-width: 300px;\n            padding: 20px;\n            border-right: 1px solid #eee;\n        }\n\n        .knowledge-section {\n            flex: 1;\n            min-width: 300px;\n            padding: 20px;\n            background-color: #f9f9f9;\n            border-radius: 10px;\n        }\n\n        .section-title {\n            color: #ff416c;\n            margin-bottom: 20px;\n            padding-bottom: 10px;\n            border-bottom: 2px solid #ff416c;\n            font-size: 1.8rem;\n        }\n\n        .equation-display {\n            font-size: 2.5rem;\n            text-align: center;\n            margin: 30px 0;\n            font-weight: bold;\n            color: #2575fc;\n            min-height: 80px;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n        }\n\n        .controls {\n            display: flex;\n            flex-direction: column;\n            gap: 15px;\n            margin: 20px 0;\n        }\n\n        button {\n            background: linear-gradient(90deg, #2575fc, #6a11cb);\n            color: white;\n            border: none;\n            padding: 15px 20px;\n            border-radius: 50px;\n            font-size: 1.1rem;\n            cursor: pointer;\n            transition: all 0.3s ease;\n            font-weight: bold;\n            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);\n        }\n\n        button:hover {\n            transform: translateY(-3px);\n            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);\n        }\n\n        button:active {\n            transform: translateY(1px);\n        }\n\n        .solution-steps {\n            background-color: #e3f2fd;\n            border-radius: 10px;\n            padding: 20px;\n            margin: 20px 0;\n            font-size: 1.1rem;\n            line-height: 1.6;\n        }\n\n        .step {\n            margin-bottom: 15px;\n            padding-left: 20px;\n            position: relative;\n        }\n\n        .step:before {\n            content: \"→\";\n            position: absolute;\n            left: 0;\n            color: #ff416c;\n            font-weight: bold;\n        }\n\n        .answer-input {\n            display: flex;\n            flex-direction: column;\n            gap: 10px;\n            margin: 20px 0;\n        }\n\n        label {\n            font-size: 1.2rem;\n            font-weight: bold;\n            color: #2575fc;\n        }\n\n        input {\n            padding: 15px;\n            border: 2px solid #ddd;\n            border-radius: 10px;\n            font-size: 1.2rem;\n            transition: border-color 0.3s;\n        }\n\n        input:focus {\n            border-color: #2575fc;\n            outline: none;\n            box-shadow: 0 0 0 2px rgba(37, 117, 252, 0.2);\n        }\n\n        .feedback {\n            text-align: center;\n            font-size: 1.3rem;\n            font-weight: bold;\n            padding: 15px;\n            border-radius: 10px;\n            margin: 20px 0;\n            display: none;\n        }\n\n        .correct {\n            background-color: #e8f5e9;\n            color: #2e7d32;\n            display: block;\n        }\n\n        .incorrect {\n            background-color: #ffebee;\n            color: #c62828;\n            display: block;\n        }\n\n        .knowledge-content {\n            line-height: 1.8;\n            font-size: 1.1rem;\n        }\n\n        .knowledge-content h3 {\n            color: #ff416c;\n            margin: 20px 0 10px;\n        }\n\n        .knowledge-content ul {\n            padding-left: 25px;\n            margin: 10px 0;\n        }\n\n        .knowledge-content li {\n            margin-bottom: 8px;\n        }\n\n        .example {\n            background-color: #e3f2fd;\n            padding: 15px;\n            border-radius: 10px;\n            margin: 15px 0;\n            font-style: italic;\n        }\n\n        footer {\n            text-align: center;\n            padding: 20px;\n            background-color: #f5f5f5;\n            color: #666;\n            font-size: 0.9rem;\n        }\n\n        @media (max-width: 768px) {\n            .content {\n                flex-direction: column;\n            }\n\n            .equation-section {\n                border-right: none;\n                border-bottom: 1px solid #eee;\n            }\n        }\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <header>\n            <h1>一元一次方程交互式学习工具</h1>\n            <div class=\"subtitle\">探索数学之美，掌握方程解法</div>\n        </header>\n\n        <div class=\"content\">\n            <div class=\"equation-section\">\n                <h2 class=\"section-title\">方程求解</h2>\n\n                <div class=\"equation-display\" id=\"equationDisplay\">\n                    点击生成方程按钮开始\n                </div>\n\n                <div class=\"controls\">\n                    <button id=\"generateBtn\">生成新方程</button>\n                    <button id=\"showStepsBtn\">显示解题步骤</button>\n                </div>\n\n                <div class=\"solution-steps\" id=\"solutionSteps\">\n                    <p>解题步骤将显示在这里...</p>\n                </div>\n\n                <div class=\"answer-input\">\n                    <label for=\"answer\">你的答案 (x = ?):</label>\n                    <input type=\"text\" id=\"answer\" placeholder=\"输入方程的解\">\n                    <button id=\"checkBtn\">检查答案</button>\n                </div>\n\n                <div class=\"feedback\" id=\"feedback\"></div>\n            </div>\n\n            <div class=\"knowledge-section\">\n                <h2 class=\"section-title\">知识讲解</h2>\n\n                <div class=\"knowledge-content\">\n                    <h3>什么是一元一次方程？</h3>\n                    <p>一元一次方程是只含有一个未知数（通常用x表示），且未知数的最高次数为1的方程。其标准形式为：</p>\n                    <p class=\"example\">ax + b = 0 (a ≠ 0)</p>\n\n                    <h3>解方程的基本步骤</h3>\n                    <ol>\n                        <li><strong>移项：</strong>将含有未知数的项移到等式一侧，常数项移到另一侧</li>\n                        <li><strong>合并同类项：</strong>简化等式两边</li>\n                        <li><strong>系数化为1：</strong>两边同时除以未知数的系数</li>\n                    </ol>\n\n                    <h3>重要性质</h3>\n                    <ul>\n                        <li><strong>等式性质1：</strong>等式两边同时加(减)同一个数，等式仍成立</li>\n                        <li><strong>等式性质2：</strong>等式两边同时乘(除)同一个不为零的数，等式仍成立</li>\n                        <li>方程的解是使方程左右两边相等的未知数的值</li>\n                    </ul>\n\n                    <h3>实际应用</h3>\n                    <p>一元一次方程广泛应用于日常生活：</p>\n                    <ul>\n                        <li>计算商品折扣和价格</li>\n                        <li>解决行程问题（速度、时间、距离）</li>\n                        <li>分配问题和比例问题</li>\n                        <li>解决简单的财务问题</li>\n                    </ul>\n\n                    <div class=\"example\">\n                        <p><strong>示例：</strong>小明买书，如果买5本还剩20元，买8本还差10元。问每本书多少钱？</p>\n                        <p>设每本书x元，则：5x + 20 = 8x - 10</p>\n                        <p>解方程得：x = 10（元）</p>\n                    </div>\n                </div>\n            </div>\n        </div>\n\n        <footer>\n            <p>数学教学工具 | 设计用于课堂互动学习 | © 2023 数学教育</p>\n        </footer>\n    </div>\n\n    <script>\n        // 页面元素\n        const equationDisplay = document.getElementById('equationDisplay');\n        const solutionSteps = document.getElementById('solutionSteps');\n        const generateBtn = document.getElementById('generateBtn');\n        const showStepsBtn = document.getElementById('showStepsBtn');\n        const checkBtn = document.getElementById('checkBtn');\n        const answerInput = document.getElementById('answer');\n        const feedback = document.getElementById('feedback');\n\n        // 当前方程参数\n        let a, b, solution;\n\n        // 生成随机方程\n        function generateEquation() {\n            // 生成系数a（不为0）\n            a = Math.floor(Math.random() * 10) - 5;\n            while(a === 0) {\n                a = Math.floor(Math.random() * 10) - 5;\n            }\n\n            // 生成常数b\n            b = Math.floor(Math.random() * 20) - 10;\n\n            // 计算解\n            solution = -b / a;\n\n            // 显示方程\n            displayEquation();\n\n            // 重置步骤和反馈\n            solutionSteps.innerHTML = '<p>点击\"显示解题步骤\"按钮查看详细解法...</p>';\n            feedback.className = 'feedback';\n            answerInput.value = '';\n        }\n\n        // 显示方程\n        function displayEquation() {\n            let equation = '';\n\n            // 处理a的显示\n            if(a === 1) {\n                equation += 'x';\n            } else if(a === -1) {\n                equation += '-x';\n            } else {\n                equation += a + 'x';\n            }\n\n            // 处理b的显示\n            if(b > 0) {\n                equation += ' + ' + b;\n            } else if(b < 0) {\n                equation += ' - ' + (-b);\n            }\n\n            equation += ' = 0';\n\n            equationDisplay.textContent = equation;\n        }\n\n        // 显示解题步骤\n        function showSolutionSteps() {\n            let stepsHTML = `\n                <div class=\"step\"><strong>步骤1：移项</strong><br>\n                将常数项移到等号右侧：${a}x = ${-b}</div>\n\n                <div class=\"step\"><strong>步骤2：系数化为1</strong><br>\n                两边同时除以${a}：x = ${-b} / ${a}</div>\n            `;\n\n            // 如果结果是整数，显示简化结果\n            if(Number.isInteger(solution)) {\n                stepsHTML += `\n                    <div class=\"step\"><strong>步骤3：计算结果</strong><br>\n                    x = ${solution}</div>\n                `;\n            } else {\n                // 简化分数\n                const gcd = findGCD(Math.abs(-b), Math.abs(a));\n                const numerator = -b / gcd;\n                const denominator = a / gcd;\n\n                stepsHTML += `\n                    <div class=\"step\"><strong>步骤3：化简分数</strong><br>\n                    x = ${numerator}/${denominator}</div>\n\n                    <div class=\"step\"><strong>步骤4：计算结果（小数）</strong><br>\n                    x ≈ ${solution.toFixed(4)}</div>\n                `;\n            }\n\n            solutionSteps.innerHTML = stepsHTML;\n        }\n\n        // 求最大公约数（用于分数化简）\n        function findGCD(x, y) {\n            while(y) {\n                let t = y;\n                y = x % y;\n                x = t;\n            }\n            return x;\n        }\n\n        // 检查答案\n        function checkAnswer() {\n            const userAnswer = parseFloat(answerInput.value);\n\n            if(isNaN(userAnswer)) {\n                feedback.textContent = '请输入有效的数字！';\n                feedback.className = 'feedback incorrect';\n                return;\n            }\n\n            // 允许一定的精度误差\n            if(Math.abs(userAnswer - solution) < 0.001) {\n                feedback.textContent = '✓ 正确！答案准确无误！';\n                feedback.className = 'feedback correct';\n            } else {\n                feedback.textContent = `✗ 不正确！正确答案是 ${solution.toFixed(4)}`;\n                feedback.className = 'feedback incorrect';\n            }\n        }\n\n        // 事件监听\n        generateBtn.addEventListener('click', generateEquation);\n        showStepsBtn.addEventListener('click', showSolutionSteps);\n        checkBtn.addEventListener('click', checkAnswer);\n\n        // 初始生成一个方程\n        generateEquation();\n    </script>\n</body>\n</html>"

export const test_message_2 = [
    new TextMessage({
        "id": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47",
        "role": MessageRole.User,
        "content": "根据如下内容创建可供运行的 temprature_plot.py 文件， { \"name\": \"files\", \"arguments\": { \"operation\": \"write\", \"path\": \"temperature_plot.py\", \"content\": \"import matplotlib.pyplot as plt\\ \\ # 北京近五天的温度数据\\ dates = ['07/15', '07/16', '07/17', '07/18', '07/19']\\ high_temps = [29, 32, 35, 37, 36]\\ low_temps = [23, 23, 25, 27, 26]\\ \\ # 创建图形\\ plt.figure(figsize=(10, 6))\\ \\ # 绘制最高温度折线\\ plt.plot(dates, high_temps, label='最高温度', marker='o')\\ \\ # 绘制最低温度折线\\ plt.plot(dates, low_temps, label='最低温度', marker='o')\\ \\ # 添加标题和标签\\ plt.title('北京近五天温度变化')\\ plt.xlabel('日期')\\ plt.ylabel('温度 (°C)')\\ plt.legend()\\ \\ # 保存图形\\ plt.savefig('temperature_plot.png')\\ \\ # 显示图形\\ plt.show()\" } }",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new TextMessage({
        "id": "run-22e7414f-33b6-458c-bd72-ab216e88547a",
        "role": MessageRole.Assistant,
        "content": "我理解您的请求。请问还有什么我可以帮助您的吗？",
        "parentMessageId": "run-22e7414f-33b6-458c-bd72-ab216e88547a",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-dd6d9ec3bbdc4ebd9f9bf61f573548cf",
        "name": "files",
        "arguments": {
            "operation": "write",
            "path": "temperature_plot.py",
            "content": "import matplotlib.pyplot as plt\\n\\n# 北京近五天的温度数据\\ndates = ['07/15', '07/16', '07/17', '07/18', '07/19']\\nhigh_temps = [29, 32, 35, 37, 36]\\nlow_temps = [23, 23, 25, 27, 26]\\n\\n# 创建图形\\nplt.figure(figsize=(10, 6))\\n\\n# 绘制最高温度折线\\nplt.plot(dates, high_temps, label='最高温度', marker='o')\\n\\n# 绘制最低温度折线\\nplt.plot(dates, low_temps, label='最低温度', marker='o')\\n\\n# 添加标题和标签\\nplt.title('北京近五天温度变化')\\nplt.xlabel('日期')\\nplt.ylabel('温度 (°C)')\\nplt.legend()\\n\\n# 保存图形\\nplt.savefig('temperature_plot.png')\\n\\n# 显示图形\\nplt.show()"
        },
        "parentMessageId": "run-22e7414f-33b6-458c-bd72-ab216e88547a",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "df10e55f-c335-42d9-85f3-8fa9df262eca",
        "result": "文件 'temperature_plot.py' 完全重写成功",
        "actionExecutionId": "chatcmpl-tool-dd6d9ec3bbdc4ebd9f9bf61f573548cf",
        "actionName": "files",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-a7116f63-244a-4a1c-8aed-f60660144456",
        "role": MessageRole.Assistant,
        "content": "## 文件创建完成\n\n文件 `temperature_plot.py` 已成功创建，并包含所需的温度数据绘图代码。接下来，您可以通过运行该文件生成温度变化图。\n\n### 下一步计划\n1. **运行 `temperature_plot.py` 文件**：使用 Python 运行该脚本文件，生成温度变化图并保存到 `temperature_plot.png`。\n2. **验证图形文件**：确保图形文件正确生成并保存。\n\n### 执行命令\n接下来，我将使用 Python 运行 `temperature_plot.py` 文件。\n\n```python\npython temperature_plot.py\n```\n\n### 运行脚本\n现在，我将执行上述命令以生成图形。\n",
        "parentMessageId": "run-a7116f63-244a-4a1c-8aed-f60660144456",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-2ede3612fc8a4236adb8d027e48bfb34",
        "name": "execute_command",
        "arguments": {
            "command": "python temperature_plot.py",
            "folder": null,
            "background": false,
            "timeout": 60
        },
        "parentMessageId": "run-a7116f63-244a-4a1c-8aed-f60660144456",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "e2e1075c-43a9-4832-a00a-1197cf82f896",
        "result": "Status: Failed (Exit Code: 1)\n--- Standard Error ---\n  File \"/home/user/temperature_plot.py\", line 1\n    import matplotlib.pyplot as plt\\n\\n# 北京近五天的温度数据\\ndates = ['07/15', '07/16', '07/17', '07/18', '07/19']\\nhigh_temps = [29, 32, 35, 37, 36]\\nlow_temps = [23, 23, 25, 27, 26]\\n\\n# 创建图形\\nplt.figure(figsize=(10, 6))\\n\\n# 绘制最高温度折线\\nplt.plot(dates, high_temps, label='最高温度', marker='o')\\n\\n# 绘制最低温度折线\\nplt.plot(dates, low_temps, label='最低温度', marker='o')\\n\\n# 添加标题和标签\\nplt.title('北京近五天温度变化')\\nplt.xlabel('日期')\\nplt.ylabel('温度 (°C)')\\nplt.legend()\\n\\n# 保存图形\\nplt.savefig('temperature_plot.png')\\n\\n# 显示图形\\nplt.show()\n                                    ^\nSyntaxError: unexpected character after line continuation character\n\n--- Error Message ---\nexit status 1",
        "actionExecutionId": "chatcmpl-tool-2ede3612fc8a4236adb8d027e48bfb34",
        "actionName": "execute_command",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-d2ec147e-3a76-4d7c-8248-4a9c09b6f00d",
        "role": MessageRole.Assistant,
        "content": "## 错误分析与修复\n\n在执行 `temperature_plot.py` 脚本时，遇到了语法错误。错误信息指出在第 1 行的行尾有意外的字符，这通常是由于不必要的转义字符引起的。\n\n### 错误原因\n在写入文件时，内容中的换行符被错误地转义了。例如，`\n` 被错误地写入文件，而不是实际的换行符。\n\n### 修复方案\n我将修正文件内容，去除多余的转义字符，并重新写入文件。\n\n### 修正文件内容\n```python\nimport matplotlib.pyplot as plt\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\n\n# 北京近五天的温度数据\ndates = ['07/15', '07/16', '07/17', '07/18', '07/19']\nhigh_temps = [29, 32, 35, 37, 36]\nlow_temps = [23, 23, 25, 27, 26]\n\n# 创建图形\nplt.figure(figsize=(10, 6))\n\n# 绘制最高温度折线\nplt.plot(dates, high_temps, label='最高温度', marker='o')\n\n# 绘制最低温度折线\nplt.plot(dates, low_temps, label='最低温度', marker='o')\n\n# 添加标题和标签\nplt.title('北京近五天温度变化')\nplt.xlabel('日期')\nplt.ylabel('温度 (°C)')\nplt.legend()\n\n# 保存图形\nplt.savefig('temperature_plot.png')\n\n# 显示图形\nplt.show()\n```\n\n### 重新写入文件\n我将重新写入 `temperature_plot.py` 文件，然后再次运行脚本。\n",
        "parentMessageId": "run-d2ec147e-3a76-4d7c-8248-4a9c09b6f00d",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-350b8a65a7fe484cad6e1668e7bb1632",
        "name": "files",
        "arguments": {
            "operation": "write",
            "path": "temperature_plot.py",
            "content": "import matplotlib.pyplot as plt\n\n# 北京近五天的温度数据\ndates = ['07/15', '07/16', '07/17', '07/18', '07/19']\nhigh_temps = [29, 32, 35, 37, 36]\nlow_temps = [23, 23, 25, 27, 26]\n\n# 创建图形\nplt.figure(figsize=(10, 6))\n\n# 绘制最高温度折线\nplt.plot(dates, high_temps, label='最高温度', marker='o')\n\n# 绘制最低温度折线\nplt.plot(dates, low_temps, label='最低温度', marker='o')\n\n# 添加标题和标签\nplt.title('北京近五天温度变化')\nplt.xlabel('日期')\nplt.ylabel('温度 (°C)')\nplt.legend()\n\n# 保存图形\nplt.savefig('temperature_plot.png')\n\n# 显示图形\nplt.show()"
        },
        "parentMessageId": "run-d2ec147e-3a76-4d7c-8248-4a9c09b6f00d",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-350b8a65a1fe484cad6e1668e7bb1632",
        "name": "files",
        "arguments": {
            "operation": "write",
            "path": "画图.html",
            "content": text_html_1
        },
        "parentMessageId": "run-d2ec147e-3a76-4d7c-8248-4a9c09b6f00d",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-350b8a75a7fe484cad6e1668e7bb1632",
        "name": "files",
        "arguments": {
            "name": "画图.pdf",
            "path": "沙箱路径",
            "date": "2025-08-19 00:00:00"
        },
        "parentMessageId": "run-d2ec147e-3a76-4d7c-8248-4a9c09b6f00d",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "04b55985-ea00-4740-b181-fe8827deaf20",
        "result": "文件 'temperature_plot.py' 完全重写成功",
        "actionExecutionId": "chatcmpl-tool-350b8a65a7fe484cad6e1668e7bb1632",
        "actionName": "files",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-820e0ca8-a736-4a0c-8554-3d5ffce9cb7a",
        "role": MessageRole.Assistant,
        "content": "## 文件重新创建完成\n\n文件 `temperature_plot.py` 已成功重新创建，并修正了之前的语法错误。接下来，我将再次运行该文件以生成温度变化图。\n\n### 执行命令\n```python\npython temperature_plot.py\n```\n\n### 运行脚本\n现在，我将执行上述命令以生成图形。\n",
        "parentMessageId": "run-820e0ca8-a736-4a0c-8554-3d5ffce9cb7a",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-7206c791460d4367ad5e3f698c5f7ddc",
        "name": "execute_command",
        "arguments": {
            "command": "python temperature_plot.py",
            "folder": null,
            "background": false,
            "timeout": 60
        },
        "parentMessageId": "run-820e0ca8-a736-4a0c-8554-3d5ffce9cb7a",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "4f3afa7a-e874-4932-9c39-ecfd5f8ed94c",
        "result": "Status: Success (Exit Code: 0)\n--- Standard Error ---\n/home/user/temperature_plot.py:24: UserWarning: Glyph 28201 (\\N{CJK UNIFIED IDEOGRAPH-6E29}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 24230 (\\N{CJK UNIFIED IDEOGRAPH-5EA6}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 21271 (\\N{CJK UNIFIED IDEOGRAPH-5317}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 20140 (\\N{CJK UNIFIED IDEOGRAPH-4EAC}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 36817 (\\N{CJK UNIFIED IDEOGRAPH-8FD1}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 20116 (\\N{CJK UNIFIED IDEOGRAPH-4E94}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 22825 (\\N{CJK UNIFIED IDEOGRAPH-5929}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 21464 (\\N{CJK UNIFIED IDEOGRAPH-53D8}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 21270 (\\N{CJK UNIFIED IDEOGRAPH-5316}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 26085 (\\N{CJK UNIFIED IDEOGRAPH-65E5}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 26399 (\\N{CJK UNIFIED IDEOGRAPH-671F}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 26368 (\\N{CJK UNIFIED IDEOGRAPH-6700}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 39640 (\\N{CJK UNIFIED IDEOGRAPH-9AD8}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')\n/home/user/temperature_plot.py:24: UserWarning: Glyph 20302 (\\N{CJK UNIFIED IDEOGRAPH-4F4E}) missing from font(s) DejaVu Sans.\n  plt.savefig('temperature_plot.png')",
        "actionExecutionId": "chatcmpl-tool-7206c791460d4367ad5e3f698c5f7ddc",
        "actionName": "execute_command",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-53433355-540e-49e0-9a32-513e15e54897",
        "role": MessageRole.Assistant,
        "content": "## 图形生成成功\n\n文件 `temperature_plot.py` 已成功运行，并生成了温度变化图。虽然运行过程中出现了一些警告信息，提示某些中文字符在默认字体中缺失，但这不影响图形的生成和显示。\n\n### 生成的图形文件\n- **`temperature_plot.png`**：北京近五天温度变化图\n\n### 下一步计划\n1. **验证图形文件**：读取并显示生成的 `temperature_plot.png` 文件。\n2. **分享图形文件**：将生成的图形文件分享给您。\n\n### 读取并显示文件\n我现在将读取并显示 `temperature_plot.png` 文件。\n",
        "parentMessageId": "run-53433355-540e-49e0-9a32-513e15e54897",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-b6f4df54bf8f4d12b5873f0c222ee140",
        "name": "message",
        "arguments": {
            "operation": "ask",
            "text": "已经成功生成了北京近五天温度变化图。请查看附带的 `temperature_plot.png` 文件。",
            "attachments": [
                "temperature_plot.png"
            ]
        },
        "parentMessageId": "run-53433355-540e-49e0-9a32-513e15e54897",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "d10fe83d-1e74-496b-a739-a3233e0fa757",
        "result": "已向用户提问，请等待用户回应",
        "actionExecutionId": "chatcmpl-tool-b6f4df54bf8f4d12b5873f0c222ee140",
        "actionName": "message",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run-e0fcc75c-0fb8-4677-bebb-f101bbbb5297",
        "role": MessageRole.Assistant,
        "content": "## 图形文件已生成并分享\n\n已经成功生成了北京近五天温度变化图。请查看附带的 `temperature_plot.png` 文件。\n\n![temperature_plot.png](temperature_plot.png)\n\n如果您有任何其他需求或需要进一步的修改，请告诉我。",
        "parentMessageId": "run-e0fcc75c-0fb8-4677-bebb-f101bbbb5297",
        "createdAt": "2025-08-01T07:43:33.477Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    })
];

export const test_message_web_search = [
    new TextMessage({
        "id": "ck-7ed7c155-dab3-4faf-95b5-e769c9691831",
        "role": MessageRole.User,
        "content": "搜索一下北京5天的天气",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new AgentStateMessage({
        "id": "ck-4eb53010-7db2-48de-a1fa-d17adace764f",
        "threadId": "8b9a77cf-a335-4807-b9f1-b265dbb12a57",
        "role": MessageRole.Assistant,
        "agentName": "agent",
        "nodeName": "__end__",
        "runId": "1f071459-1a2d-63c4-a5d6-f66dc7b5f07b",
        "active": false,
        "running": true,
        "state": {
            "messages": [
                {
                    "role": "user",
                    "content": "搜索一下北京5天的天气",
                    "id": "ck-7ed7c155-dab3-4faf-95b5-e769c9691831"
                },
                {
                    "role": "assistant",
                    "content": "## 规划\n\n为了获取北京未来5天的天气预报，我将按照以下步骤进行：\n\n1. **网络搜索**：使用 `web` 工具执行网络搜索，找到可靠的天气预报网站。\n2. **内容提取**：从搜索结果中提取相关网站的URL，然后使用 `web` 工具的 `scrape` 操作来抓取具体的内容。\n3. **数据解析**：解析抓取到的数据，提取出未来5天的天气信息。\n4. **结果展示**：将提取到的天气信息整理成易于阅读的格式，并提供给用户。\n\n现在开始第一步，使用 `web` 工具进行网络搜索。\n\n",
                    "id": "run--c395d870-ee5f-4593-9c68-d3ee26fd6e39",
                    "parentMessageId": "run--c395d870-ee5f-4593-9c68-d3ee26fd6e39"
                },
                {
                    "role": "assistant",
                    "content": "我理解您的请求。请问还有什么我可以帮助您的吗？",
                    "id": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
                    "parentMessageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f"
                },
                {
                    "id": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
                    "name": "web",
                    "arguments": {
                        "operation": "search",
                        "sub_queries": [
                            {
                                "query": "北京 未来5天 天气预报",
                                "topic": "general",
                                "days": 3
                            }
                        ]
                    },
                    "parentMessageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f"
                },
                {
                    "actionExecutionId": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
                    "actionName": "web",
                    "result": "搜索发现以下新文档:\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845): 简介: 2025年08月04日北京天气预报:\n08/04 (周一):\n天气:中雨,温度:28/23°C,风向风力:东南风<3级\n08/05 (周二):\n天气:多云,温度:31/23°C,风向风力:南风<3级\n08/06 (周三):\n天气:多云转晴,温度:33/24°C,风向风力:西北风<3级\n08/07 (周四):\n天气:多云,温度:32/24°C,风向风力:西南风<3级\n08/08 (周五):\n天气:阴转雷阵雨,温度:28/22°C,风向风力:北风<3级\n08/09 (周六):\n天气:小雨,温度:29/22°C,风向风力:东风<3级\n08/10 (周日):\n天气:多云转晴,温度:30/22°C,风向...\n- [2025年08月04日政和天气预报](https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e): 简介: 2025年08月04日政和天气预报:\n08/04 (周一):\n天气:小雨转多云,温度:35/24°C,风向风力:无持续风向<3级\n08/05 (周二):\n天气:小雨转多云,温度:34/23°C,风向风力:无持续风向<3级\n08/06 (周三):\n天气:小雨转多云,温度:33/23°C,风向风力:无持续风向<3级\n08/07 (周四):\n天气:多云,温度:35/24°C,风向风力:无持续风向<3级\n08/08 (周五):\n天气:多云,温度:36/24°C,风向风力:无持续风向<3级\n08/09 (周六):\n天气:多云,温度:37/25°C,风向风力:无持续风向<3级\n08/10 (周日):\n天气...",
                    "id": "ab0b278a-f632-42cf-97ef-703d659ed35c"
                },
                {
                    "role": "assistant",
                    "content": "## 搜索结果分析\n\n根据搜索结果，我找到了一个可靠的天气预报网站，提供了北京未来5天的天气预报信息。以下是具体的天气情况：\n\n### 北京未来5天天气预报\n\n- **08/05 (周二)**:\n  - 天气: 多云\n  - 温度: 31/23°C\n  - 风向风力: 南风 <3级\n\n- **08/06 (周三)**:\n  - 天气: 多云转晴\n  - 温度: 33/24°C\n  - 风向风力: 西北风 <3级\n\n- **08/07 (周四)**:\n  - 天气: 多云\n  - 温度: 32/24°C\n  - 风向风力: 西南风 <3级\n\n- **08/08 (周五)**:\n  - 天气: 阴转雷阵雨\n  - 温度: 28/22°C\n  - 风向风力: 北风 <3级\n\n- **08/09 (周六)**:\n  - 天气: 小雨\n  - 温度: 29/22°C\n  - 风向风力: 东风 <3级\n\n### 数据来源\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845)\n\n如果您需要更多详细信息或有其他问题，请告诉我！",
                    "id": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4",
                    "parentMessageId": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4"
                }
            ],
            "copilotkit": {
                "actions": []
            },
            "logs": [
                {
                    "message": "🌐 正在打开浏览器)",
                    "done": true,
                    "messageId": "run--c395d870-ee5f-4593-9c68-d3ee26fd6e39",
                },
                {
                    "message": "🌐 正在搜索网络",
                    "done": true,
                    "messageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
                },
                {
                    "message": "🌐 正在搜索网络3333",
                    "done": true,
                    "messageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
                },
                {
                    "message": "🌐 正在搜索网络444",
                    "done": true,
                    "messageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
                },
                {
                    "message": "🌐 正在查看结果",
                    "done": true,
                    "messageId": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4",
                }
            ],
            "e2b_sandbox_id": "",
            "temporary_message_content_list": [],
            "iteration_count": 0,
            "max_iterations": 150,
            "temporary_images": [],
            "structure_tool_results": {
                "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96": {
                    "https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845#bocha": {
                        "url": "https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845",
                        "title": "2025年08月04日北京天气预报",
                        "content": "2025年08月04日北京天气预报:\n08/04 (周一):\n天气:中雨,温度:28/23°C,风向风力:东南风<3级\n08/05 (周二):\n天气:多云,温度:31/23°C,风向风力:南风<3级\n08/06 (周三):\n天气:多云转晴,温度:33/24°C,风向风力:西北风<3级\n08/07 (周四):\n天气:多云,温度:32/24°C,风向风力:西南风<3级\n08/08 (周五):\n天气:阴转雷阵雨,温度:28/22°C,风向风力:北风<3级\n08/09 (周六):\n天气:小雨,温度:29/22°C,风向风力:东风<3级\n08/10 (周日):\n天气:多云转晴,温度:30/22°C,风向",
                        "provider": "bocha",
                        "score": 0
                    },
                    "https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e#bocha": {
                        "url": "https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e",
                        "title": "2025年08月04日政和天气预报",
                        "content": "2025年08月04日政和天气预报:\n08/04 (周一):\n天气:小雨转多云,温度:35/24°C,风向风力:无持续风向<3级\n08/05 (周二):\n天气:小雨转多云,温度:34/23°C,风向风力:无持续风向<3级\n08/06 (周三):\n天气:小雨转多云,温度:33/23°C,风向风力:无持续风向<3级\n08/07 (周四):\n天气:多云,温度:35/24°C,风向风力:无持续风向<3级\n08/08 (周五):\n天气:多云,温度:36/24°C,风向风力:无持续风向<3级\n08/09 (周六):\n天气:多云,温度:37/25°C,风向风力:无持续风向<3级\n08/10 (周日):\n天气",
                        "provider": "bocha",
                        "score": 0
                    }
                }
            },
            "completed": false,
            "mcp_tools": [],
            "input_data": {},
            "model": "Qwen2.5-72B-Instruct",
            "a2a_agents": [],
            "a2a_sessions": {},
            "a2a_failure_count": 0,
            "a2a_fallback_to_general": true,
            "failed_a2a_agents": [],
            "supervisor_retry_count": 0,
            "supervisor_decision": {},
            "current_step_completed": true,
            "workflow_steps": [],
            "current_step_index": 3,
            "execution_results": {
                "general_agent_single_step": {
                    "agent_name": "通用智能体",
                    "result": "## 搜索结果分析\n\n根据搜索结果，我找到了一个可靠的天气预报网站，提供了北京未来5天的天气预报信息。以下是具体的天气情况：\n\n### 北京未来5天天气预报\n\n- **08/05 (周二)**:\n  - 天气: 多云\n  - 温度: 31/23°C\n  - 风向风力: 南风 <3级\n\n- **08/06 (周三)**:\n  - 天气: 多云转晴\n  - 温度: 33/24°C\n  - 风向风力: 西北风 <3级\n\n- **08/07 (周四)**:\n  - 天气: 多云\n  - 温度: 32/24°C\n  - 风向风力: 西南风 <3级\n\n- **08/08 (周五)**:\n  - 天气: 阴转雷阵雨\n  - 温度: 28/22°C\n  - 风向风力: 北风 <3级\n\n- **08/09 (周六)**:\n  - 天气: 小雨\n  - 温度: 29/22°C\n  - 风向风力: 东风 <3级\n\n### 数据来源\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845)\n\n如果您需要更多详细信息或有其他问题，请告诉我！",
                    "timestamp": "2025-08-04T15:14:14.091711",
                    "success": true,
                    "step_id": 3
                }
            }
        },
        "createdAt": "2025-08-04T15:14:13.673Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "AgentStateMessage"
    }),
    new TextMessage({
        "id": "run--c395d870-ee5f-4593-9c68-d3ee26fd6e39",
        "role": MessageRole.Assistant,
        "content": "## 规划\n\n为了获取北京未来5天的天气预报，我将按照以下步骤进行：\n\n1. **网络搜索**：使用 `web` 工具执行网络搜索，找到可靠的天气预报网站。\n2. **内容提取**：从搜索结果中提取相关网站的URL，然后使用 `web` 工具的 `scrape` 操作来抓取具体的内容。\n3. **数据解析**：解析抓取到的数据，提取出未来5天的天气信息。\n4. **结果展示**：将提取到的天气信息整理成易于阅读的格式，并提供给用户。\n\n现在开始第一步，使用 `web` 工具进行网络搜索。\n\n",
        "parentMessageId": "run--c395d870-ee5f-4593-9c68-d3ee26fd6e39",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-a64041e255154a94a21d0a2491d062e3",
        "name": "files",
        "arguments": {
            "name": "测试文件.xlsx",
            "path": "测试文件.xlsx"
        },
        "parentMessageId": "run--e99f0cef-af1b-4cb4-97e5-688a9613717a",
        "createdAt": "2025-08-24T14:26:05.618Z",
        "status": {
            "code": MessageStatusCode.Success,
            "__typename": "SuccessMessageStatus"
        },
        "type": "ActionExecutionMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-a64042e255154a94a21d0a2491d062e3",
        "name": "execute_command",
        "arguments": {
            "command": "pip install requests beautifulsoup4 matplotlib",
            "folder": null,
            "background": false,
            "timeout": 60
        },
        "parentMessageId": "run--e99f0cef-af1b-4cb4-97e5-688a9613717a",
        "createdAt": "2025-08-24T14:26:05.618Z",
        "status": {
            "code": MessageStatusCode.Success,
            "__typename": "SuccessMessageStatus"
        },
        "type": "ActionExecutionMessage"
    }),
    new TextMessage({
        "id": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
        "role": MessageRole.Assistant,
        "content": "我理解您的请求。请问还有什么我可以帮助您的吗？",
        "parentMessageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
        "name": "web",
        "arguments": {
            "operation": "search",
            "sub_queries": [
                {
                    "query": "北京 未来5天 天气预报",
                    "topic": "general",
                    "days": 3
                }
            ]
        },
        "parentMessageId": "run--5a674231-95cd-4375-901f-c9ea9eab990f",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new ActionExecutionMessage({
        "id": "chatcmpl-tool-ca1926a688e54a9a8ebd3dffb1bb1254",
        "name": "execute_command",
        "arguments": {
            "command": "python weather_script.py",
            "folder": null,
            "background": false,
            "timeout": 60
        },
        "parentMessageId": "run--1795c470-cb84-4e01-8e3b-6c2cda25e619",
        "createdAt": "2025-08-24T14:26:05.618Z",
        "status": {
            "code": MessageStatusCode.Success,
            "__typename": "SuccessMessageStatus"
        },
        "type": "ActionExecutionMessage"
    }),
    new ResultMessage({
        "id": "ab0b278a-f632-42cf-97ef-703d659ed35c",
        "result": "搜索发现以下新文档:\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845): 简介: 2025年08月04日北京天气预报:\n08/04 (周一):\n天气:中雨,温度:28/23°C,风向风力:东南风<3级\n08/05 (周二):\n天气:多云,温度:31/23°C,风向风力:南风<3级\n08/06 (周三):\n天气:多云转晴,温度:33/24°C,风向风力:西北风<3级\n08/07 (周四):\n天气:多云,温度:32/24°C,风向风力:西南风<3级\n08/08 (周五):\n天气:阴转雷阵雨,温度:28/22°C,风向风力:北风<3级\n08/09 (周六):\n天气:小雨,温度:29/22°C,风向风力:东风<3级\n08/10 (周日):\n天气:多云转晴,温度:30/22°C,风向...\n- [2025年08月04日政和天气预报](https://bochaai.com/share/ed82b3d5-4440-47a4-b8cf-8879b1c97b1e): 简介: 2025年08月04日政和天气预报:\n08/04 (周一):\n天气:小雨转多云,温度:35/24°C,风向风力:无持续风向<3级\n08/05 (周二):\n天气:小雨转多云,温度:34/23°C,风向风力:无持续风向<3级\n08/06 (周三):\n天气:小雨转多云,温度:33/23°C,风向风力:无持续风向<3级\n08/07 (周四):\n天气:多云,温度:35/24°C,风向风力:无持续风向<3级\n08/08 (周五):\n天气:多云,温度:36/24°C,风向风力:无持续风向<3级\n08/09 (周六):\n天气:多云,温度:37/25°C,风向风力:无持续风向<3级\n08/10 (周日):\n天气...",
        "actionExecutionId": "chatcmpl-tool-667cb6d690794fa9b4e5dcdbf6ee0c96",
        "actionName": "web",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ResultMessage"
    }),
    new TextMessage({
        "id": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4",
        "role": MessageRole.Assistant,
        "content": "## 搜索结果分析\n\n根据搜索结果，我找到了一个可靠的天气预报网站，提供了北京未来5天的天气预报信息。以下是具体的天气情况：\n\n### 北京未来5天天气预报\n\n- **08/05 (周二)**:\n  - 天气: 多云\n  - 温度: 31/23°C\n  - 风向风力: 南风 <3级\n\n- **08/06 (周三)**:\n  - 天气: 多云转晴\n  - 温度: 33/24°C\n  - 风向风力: 西北风 <3级\n\n- **08/07 (周四)**:\n  - 天气: 多云\n  - 温度: 32/24°C\n  - 风向风力: 西南风 <3级\n\n- **08/08 (周五)**:\n  - 天气: 阴转雷阵雨\n  - 温度: 28/22°C\n  - 风向风力: 北风 <3级\n\n- **08/09 (周六)**:\n  - 天气: 小雨\n  - 温度: 29/22°C\n  - 风向风力: 东风 <3级\n\n### 数据来源\n- [2025年08月04日北京天气预报](https://bochaai.com/share/81648f5e-2a2b-4137-a9ca-8e2e114d3845)\n\n如果您需要更多详细信息或有其他问题，请告诉我！",
        "parentMessageId": "run--b7d21865-cde2-4d03-bd6b-1cf4548abec4",
        "createdAt": "2025-08-04T15:14:13.675Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    })
]

export const test_message_web = [
    new TextMessage({
        "id": "ck-0d3e9f43-4f34-4f22-a315-870da4cdedf1",
        "role": MessageRole.User,
        "content": "帮我做一个一元一次方程的可交互学习html文件，用于上课",
        "createdAt": "2025-08-06T02:16:15.633Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new TextMessage({
        "id": "6338badf-8213-4362-9b15-d0609092a20f",
        "role": MessageRole.Assistant,
        "content": "",
        "parentMessageId": "6338badf-8213-4362-9b15-d0609092a20f",
        "createdAt": "2025-08-06T02:16:15.633Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    }),
    new ActionExecutionMessage({
        "id": "",
        "name": "files",
        "arguments": {
            "content": text_html_1,
            "operation": "write",
            "path": "帮我做一个一元一次方程的可交互学习html文件_用于上课_1754446054.html"
        },
        "parentMessageId": "6338badf-8213-4362-9b15-d0609092a20f",
        "createdAt": "2025-08-06T02:16:15.633Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "ActionExecutionMessage"
    }),
    new TextMessage({
        "id": "dfb4735a-53bd-4735-9c1f-7b4ad6769a4c",
        "role": MessageRole.Assistant,
        "content": "✅ **HTML文件处理和保存完成**\n\n**文件信息**:\n- 文件名: `帮我做一个一元一次方程的可交互学习html文件_用于上课_1754446054.html`\n- 文件大小: 12446 字符\n- 保存位置: 沙箱根目录\n- 提取方式: markdown代码块\n\n**处理步骤**:\n1. ✅ 从原始内容中提取HTML代码\n2. ✅ 清理和格式化HTML内容  \n3. ✅ 验证HTML结构完整性\n4. ✅ 保存到沙箱文件系统\n\n\n✅ **文件验证**: 文件已成功创建并可读取\n\n**使用方法**:\n1. 文件已保存在沙箱环境中\n2. 可以使用文件工具查看或操作HTML文件\n3. 在浏览器中打开查看效果\n\n**HTML内容预览** (前500字符):\n```html\n<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>一元一次方程交互式学习工具</title>\n    <style>\n        * {\n            box-sizing: border-box;\n            margin: 0;\n            padding: 0;\n            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n        }\n\n        body {\n            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);\n            min-height: 100vh;\n         ...\n```\n\n**详细保存结果**: 文件 '帮我做一个一元一次方程的可交互学习html文件_用于上课_1754446054.html' 创建成功",
        "parentMessageId": "dfb4735a-53bd-4735-9c1f-7b4ad6769a4c",
        "createdAt": "2025-08-06T02:16:15.633Z",
        "status": {
            "code": MessageStatusCode.Success
        },
        "type": "TextMessage"
    })
]

export const test_message = [
    {
        "id": "ck-216c7e29-1747-4bf4-bb07-6e494d7248dd",
        "role": "user",
        "content": "帮我查一下北京近五天天气，并将最高气温绘制一张折线图，最终生成一个报告输出。"
    },
    {
        "id": "ck-1dd304b0-0379-4da4-ba72-5cb3ac657ce8",
        "role": "assistant",
        "agentName": "agent",
        "state": {
            "messages": [
                {
                    "role": "user",
                    "content": "帮我查一下北京近五天天气，并将最高气温绘制一张折线图，最终生成一个报告输出。",
                    "id": "ck-216c7e29-1747-4bf4-bb07-6e494d7248dd"
                },
                {
                    "role": "assistant",
                    "content": "为了完成这个任务，我们将按照以下步骤进行：\n\n1. **搜索北京近五天的天气信息**：使用`tavily_tool`进行搜索。\n2. **提取最高气温数据**：从搜索结果中提取每天的最高气温。\n3. **生成折线图**：虽然我们不能直接生成图表，但我们可以描述如何生成图表。\n4. **编写报告**：将所有信息汇总成一个报告。\n\n### Step 1: 搜索北京近五天的天气信息\n\n我们将使用`tavily_tool`进行搜索，关键词为“北京 近五天 天气”。\n\n",
                    "id": "run--411c6760-bda8-4000-8a4e-6ea0c0610f92",
                    "parentMessageId": "run--411c6760-bda8-4000-8a4e-6ea0c0610f92"
                },
                {
                    "id": "chatcmpl-tool-f5411d33ea3347c980aca7447716b3ae",
                    "name": "web",
                    "arguments": {
                        "operation": "search",
                        "sub_queries": [
                            {
                                "query": "北京 近五天 天气",
                                "topic": "general",
                                "days": 5
                            }
                        ]
                    },
                    "parentMessageId": "run--411c6760-bda8-4000-8a4e-6ea0c0610f92"
                },
                {
                    "role": "assistant",
                    "content": "### Step 2: 提取最高气温数据\n\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n### Step 3: 生成折线图\n\n虽然我们不能直接生成图表，但你可以使用这些数据在任何图表工具（如Excel、Google Sheets或Python的Matplotlib库）中生成折线图。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n### Step 4: 编写报告\n\n#### 报告：北京近五天天气及最高气温\n\n**概述**：\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n**天气信息**：\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n**折线图**：\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。\n\n**结论**：\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。",
                    "id": "run--a50aeaf9-1fec-4884-8d65-b610ddebe5a7",
                    "parentMessageId": "run--a50aeaf9-1fec-4884-8d65-b610ddebe5a7"
                },
                {
                    "role": "assistant",
                    "content": "### 报告：北京近五天天气及最高气温\n\n#### 概述\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n#### 天气信息\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n#### 折线图\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n#### 结论\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。",
                    "id": "run--518011c3-c618-4d13-8dd0-bd27d398cbde",
                    "parentMessageId": "run--518011c3-c618-4d13-8dd0-bd27d398cbde"
                }
            ],
            "copilotkit": {
                "actions": []
            },
            "logs": [
                {
                    "message": "正在思考中...",
                    "done": true
                },
                {
                    "message": "研究智能体执行中",
                    "done": true
                },
                {
                    "message": "正在思考中...",
                    "done": true
                },
                {
                    "message": "研究智能体执行中",
                    "done": true
                },
                {
                    "message": "正在思考中...",
                    "done": true
                },
                {
                    "message": "报告智能体执行中",
                    "done": true
                }
            ],
            "inner_messages": [
                {
                    "content": "帮我查一下北京近五天天气，并将最高气温绘制一张折线图，最终生成一个报告输出。",
                    "additional_kwargs": {
                        "type": "TextMessage",
                        "createdAt": "2025-08-24T04:18:52.871Z"
                    },
                    "response_metadata": {},
                    "type": "human",
                    "name": null,
                    "id": "ck-216c7e29-1747-4bf4-bb07-6e494d7248dd",
                    "example": false
                },
                {
                    "content": "next:researcher",
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "type": "ai",
                    "name": "supervisor",
                    "id": "ea30778f-c727-4b94-8d51-6e21ce6fc790",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "为了完成这个任务，我们将按照以下步骤进行：\n\n1. **搜索北京近五天的天气信息**：使用`tavily_tool`进行搜索。\n2. **提取最高气温数据**：从搜索结果中提取每天的最高气温。\n3. **生成折线图**：虽然我们不能直接生成图表，但我们可以描述如何生成图表。\n4. **编写报告**：将所有信息汇总成一个报告。\n\n### Step 1: 搜索北京近五天的天气信息\n\n我们将使用`tavily_tool`进行搜索，关键词为“北京 近五天 天气”。\n\n",
                    "additional_kwargs": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "chatcmpl-tool-f5411d33ea3347c980aca7447716b3ae",
                                "function": {
                                    "arguments": "{\"operation\": \"search\", \"sub_queries\": [{\"query\": \"北京 近五天 天气\", \"topic\": \"general\", \"days\": 5}]}",
                                    "name": "web"
                                },
                                "type": "function"
                            }
                        ]
                    },
                    "response_metadata": {
                        "finish_reason": "tool_calls",
                        "model_name": "panzhi_openai/Qwen2.5-72B-Instruct"
                    },
                    "type": "ai",
                    "name": "research",
                    "id": "run--411c6760-bda8-4000-8a4e-6ea0c0610f92",
                    "example": false,
                    "tool_calls": [
                        {
                            "name": "web",
                            "args": {
                                "operation": "search",
                                "sub_queries": [
                                    {
                                        "query": "北京 近五天 天气",
                                        "topic": "general",
                                        "days": 5
                                    }
                                ]
                            },
                            "id": "chatcmpl-tool-f5411d33ea3347c980aca7447716b3ae",
                            "type": "tool_call"
                        }
                    ],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "next:researcher",
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "type": "ai",
                    "name": "supervisor",
                    "id": "a5daa839-d83e-41a4-a6df-d8247825e6bb",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "### Step 2: 提取最高气温数据\n\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n### Step 3: 生成折线图\n\n虽然我们不能直接生成图表，但你可以使用这些数据在任何图表工具（如Excel、Google Sheets或Python的Matplotlib库）中生成折线图。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n### Step 4: 编写报告\n\n#### 报告：北京近五天天气及最高气温\n\n**概述**：\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n**天气信息**：\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n**折线图**：\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。\n\n**结论**：\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。",
                    "additional_kwargs": {},
                    "response_metadata": {
                        "finish_reason": "stop",
                        "model_name": "panzhi_openai/Qwen2.5-72B-Instruct"
                    },
                    "type": "ai",
                    "name": "research",
                    "id": "run--a50aeaf9-1fec-4884-8d65-b610ddebe5a7",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "next:reporter",
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "type": "ai",
                    "name": "supervisor",
                    "id": "01ccd160-61fa-4145-9503-17725c3d7984",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "### 报告：北京近五天天气及最高气温\n\n#### 概述\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n#### 天气信息\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n#### 折线图\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n#### 结论\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。",
                    "additional_kwargs": {},
                    "response_metadata": {
                        "finish_reason": "stop",
                        "model_name": "panzhi_openai/Qwen2.5-72B-Instruct"
                    },
                    "type": "ai",
                    "name": "reporter",
                    "id": "run--518011c3-c618-4d13-8dd0-bd27d398cbde",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                },
                {
                    "content": "next:FINISH",
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "type": "ai",
                    "name": "supervisor",
                    "id": "ee199ed6-8b3b-4103-ac1a-d83befa44a15",
                    "example": false,
                    "tool_calls": [],
                    "invalid_tool_calls": [],
                    "usage_metadata": null
                }
            ],
            "e2b_sandbox_id": "",
            "temporary_message_content_list": [],
            "iteration_count": 0,
            "max_iterations": 150,
            "temporary_images": [],
            "structure_tool_results": {},
            "completed": true,
            "mcp_tools": [],
            "input_data": {},
            "model": "Qwen2.5-72B-Instruct",
            "a2a_agents": [],
            "a2a_sessions": {},
            "a2a_failure_count": 0,
            "a2a_fallback_to_general": true,
            "failed_a2a_agents": [],
            "supervisor_retry_count": 0,
            "supervisor_decision": {},
            "current_step_completed": true,
            "workflow_steps": [],
            "current_step_index": 3,
            "execution_results": {
                "general_agent_single_step": {
                    "agent_name": "通用智能体",
                    "result": "### 报告：北京近五天天气及最高气温\n\n#### 概述\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n#### 天气信息\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n#### 折线图\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n#### 结论\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。",
                    "timestamp": "2025-08-24T12:19:34.656431",
                    "success": true,
                    "step_id": 3
                }
            },
            "agent_type": "normal",
            "expert_retry_count": 0,
            "expert_connection_failed": false,
            "expert_fast_route": false,
            "expert_services": {
                "write": {
                    "url": "http://10.246.162.139:9591",
                    "graph_id": "deepresearch"
                },
                "ppt": {
                    "url": "http://localhost:7002",
                    "graph_id": "ppt-expert"
                },
                "web": {
                    "url": "http://10.246.162.139:9592",
                    "graph_id": "html"
                },
                "broadcast": {
                    "url": "http://localhost:7004",
                    "graph_id": "broadcast-expert"
                }
            },
            "session_id": "default_session",
            "conversation_round": 0,
            "attachment_processed": true,
            "last_node": "reporter"
        }
    },
    {
        "id": "run--411c6760-bda8-4000-8a4e-6ea0c0610f92",
        "role": "assistant",
        "content": "为了完成这个任务，我们将按照以下步骤进行：\n\n1. **搜索北京近五天的天气信息**：使用`tavily_tool`进行搜索。\n2. **提取最高气温数据**：从搜索结果中提取每天的最高气温。\n3. **生成折线图**：虽然我们不能直接生成图表，但我们可以描述如何生成图表。\n4. **编写报告**：将所有信息汇总成一个报告。\n\n### Step 1: 搜索北京近五天的天气信息\n\n我们将使用`tavily_tool`进行搜索，关键词为“北京 近五天 天气”。\n\n"
    },
    {
        "id": "chatcmpl-tool-f5411d33ea3347c980aca7447716b3ae",
        "role": "assistant",
        "toolCalls": [
            {
                "id": "chatcmpl-tool-f5411d33ea3347c980aca7447716b3ae",
                "function": {
                    "name": "web",
                    "arguments": "{\"operation\":\"search\",\"sub_queries\":[{\"query\":\"北京 近五天 天气\",\"topic\":\"general\",\"days\":5}]}"
                },
                "type": "function"
            }
        ],
        "name": "web"
    },
    {
        "id": "run--a50aeaf9-1fec-4884-8d65-b610ddebe5a7",
        "role": "assistant",
        "content": "### Step 2: 提取最高气温数据\n\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n### Step 3: 生成折线图\n\n虽然我们不能直接生成图表，但你可以使用这些数据在任何图表工具（如Excel、Google Sheets或Python的Matplotlib库）中生成折线图。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n### Step 4: 编写报告\n\n#### 报告：北京近五天天气及最高气温\n\n**概述**：\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n**天气信息**：\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n**折线图**：\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。\n\n**结论**：\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。"
    },
    {
        "id": "run--518011c3-c618-4d13-8dd0-bd27d398cbde",
        "role": "assistant",
        "content": "### 报告：北京近五天天气及最高气温\n\n#### 概述\n本报告总结了北京近五天的天气情况，特别是每天的最高气温。\n\n#### 天气信息\n根据搜索结果，以下是北京近五天的天气信息及最高气温：\n\n- **今天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **明天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **大后天 (YYYY-MM-DD)**: 最高气温 XX°C\n- **第五天 (YYYY-MM-DD)**: 最高气温 XX°C\n\n#### 折线图\n为了更直观地展示温度变化，建议使用上述数据生成折线图。你可以使用Excel、Google Sheets或Python的Matplotlib库来生成图表。以下是一个简单的示例代码，如果你有编程经验，可以参考：\n\n```python\nimport matplotlib.pyplot as plt\n\n# 数据\ndates = ['YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD']\ntemperatures = [XX, XX, XX, XX, XX]\n\n# 绘制折线图\nplt.plot(dates, temperatures, marker='o')\nplt.xlabel('日期')\nplt.ylabel('最高气温 (°C)')\nplt.title('北京近五天最高气温')\nplt.grid(True)\nplt.show()\n```\n\n#### 结论\n北京近五天的天气预计较为稳定，最高气温在XX°C至XX°C之间波动。建议根据具体天气情况做好相应的防护措施。\n\n---\n\n希望这份报告对你有所帮助！如果有任何进一步的问题，请随时联系我。"
    }
]

export const test_message_deepinsight: Message[] = [
    {
        "id": "ck-2534549a-c37d-4dd5-b6ec-c6c6edc3ea47",
        "role": "user",
        "content": "使用deepinsight工具"
    },
    {
        "id": "dd6d9ec3bbdc5ebd9f9bf61f573548cf",
        "role": "assistant",
        "toolCalls": [
            {
                "id": "chatcmpl-tool-dd6d9ec3bbdc4ebd9f9bf61f573548cf",
                "function": {
                    "name": "deepinsight",
                    "arguments": "{}"
                },
                "type": "function"
            }
        ],
        "name": "deepinsight"
    },
    {
        "id": "run-a7116f63-244a-4a1c-8aed-f60660144456",
        "role": "assistant",
        "content": "# 现金流重构与价值跃迁：中国移动财务战略全景洞察\n## 摘要\n中国移动作为全球领先的电信运营商，其财务表现不仅反映企业自身的经营效率，也映射出通信行业在数字化转型、ESG实践、技术创新及全球化布局中的宏观趋势。本报告聚焦于中国移动近年来在应收账款管理、ESG评级提升、AI与6G技术投资、国际业务拓展以及股息可持续性等关键财务维度的动态变化，旨在揭示其财务结构的深层逻辑与未来增长潜力。在应收账款方面，尽管公司营收与利润持续增长，但应收账款周转率从23.45次下降至15.94次，反映出在扩大市场份额过程中回款效率的下滑，潜在的流动性风险值得关注。为应对这一挑战，企业需强化客户信用评估、优化催收机制并引入智能化财务管理工具。与此同时，中国移动在ESG领域表现突出，2024年华证指数评级提升至AAA级，行业排名第一，尤其在公司治理维度优势显著，这不仅增强其品牌价值与市场信心，也为长期财务稳健性提供支撑。在技术投资方面，公司加速布局AI算力与6G研发，计划2025年投入373亿元用于算力建设，AI投资两年增长超10倍，6G商用预计2030年落地，将推动全球通信市场收入增长至5.6万亿美元，AI终端与行业模组将成为新的收入增长点。国际业务方面，2023年收入达207亿元，同比增长24.2%，2024年预计进一步增长至228亿元，公司通过“一带一路”倡议与数字基建出海持续拓展全球影响力。在资本回报方面，中国移动承诺未来三年分红比例提升至75% 以上，结合年化5 % 至7.5 % 的利润增长预期与资本支出下降趋势，其高股息策略具备较强财务支撑，当前港股股息收益率已达7.1 %，估值水平显示其具备较高投资吸引力。综合来看，中国移动在多重战略驱动下，正构建一个兼具稳健性与成长性的财务体系，为长期可持续发展奠定坚实基础。\n\n### 1 引言\n中国移动作为全球用户规模最大的电信运营商之一，其财务结构与战略动向不仅关乎企业自身发展，更深刻影响着通信行业的演进路径。在数字经济加速渗透、ESG理念日益深化、技术变革持续演进的多重背景下，中国移动的财务表现呈现出多维度交织的复杂图景。本报告聚焦于其应收账款管理效率、ESG评级提升、AI与6G技术投资、国际业务增长以及高股息承诺等关键财务议题，旨在揭示其在多重战略驱动下的财务韧性与增长潜力。\n\n应收账款周转率的持续下降，是当前中国移动财务结构中一个值得关注的信号。尽管公司营收与利润保持稳健增长，但应收账款周转率从23.45次下降至15.94次，反映出在扩大市场份额过程中回款效率的下滑，潜在的流动性风险不容忽视。这一趋势背后，既有信用政策调整的主动选择，也与客户结构变化及内部管理机制的适应性不足密切相关。如何在保持市场竞争力的同时优化资金回流效率，已成为其财务管理中的关键命题。\n\n与此同时，中国移动在ESG领域的持续投入正逐步转化为财务层面的长期优势。2024年华证指数将其ESG评级提升至AAA级，位列无线电信业务行业A股上市公司第一名，尤其在公司治理维度表现突出。这一评级不"
    },
    {
        "id": "",
        "role": "assistant",
        "toolCalls": [
            {
                "id": "",
                "function": {
                    "name": "files",
                    "arguments": "{\"date\":\"2025-08-19 00:00:00\",\"path\":\"research-report-2025-11-17T06-29-45.md\",\"name\":\"research-report-2025-11-17T06-29-45.md\"}"
                },
                "type": "function"
            }
        ],
        "name": "files"
    },
    {
        "id": "run-a7116f63-244a-4a1c-8aed-f60660144456",
        "role": "assistant",
        "content": "已完成任务"
    },
]