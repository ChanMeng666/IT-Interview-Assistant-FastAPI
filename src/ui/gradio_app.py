import gradio as gr
import httpx
from typing import Dict, List
import json

# API端点配置
API_BASE_URL = "http://localhost:8000/api"

# 当前会话状态
current_session = {"id": None, "context": []}

async def start_new_interview(position_level: str, technologies: str) -> List[Dict]:
    """开始新的面试会话"""
    try:
        tech_list = [t.strip() for t in technologies.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/interview/start",
                json={"position_level": position_level, "technologies": tech_list},
                timeout=30.0
            )
            result = response.json()

            current_session["id"] = result.get("session_id")
            question = result.get("question", "让我们开始面试。请做个自我介绍。")

            # 返回 messages 格式
            return [{"role": "assistant", "content": question}]

    except Exception as e:
        print(f"Error starting interview: {e}")
        return [{"role": "assistant", "content": "抱歉，启动面试时出现错误。请稍后重试。"}]


async def submit_answer(answer: str, history: List[Dict]) -> tuple:
    """提交答案并获取下一个问题"""
    try:
        if not current_session["id"]:
            return "", history + [
                {"role": "user", "content": answer},
                {"role": "assistant", "content": "请先开始面试"}
            ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/interview/answer/{current_session['id']}",
                json={"answer": answer},
                timeout=30.0
            )
            result = response.json()

            response_text = f"评价: {result.get('evaluation', '未提供评价')}\n\n下一个问题: {result.get('next_question', '请继续。')}"

            # 返回 messages 格式
            history = history or []
            history.append({"role": "user", "content": answer})
            history.append({"role": "assistant", "content": response_text})

            return "", history
    except Exception as e:
        print(f"Error submitting answer: {e}")
        history = history or []
        history.append({"role": "user", "content": answer})
        history.append({"role": "assistant", "content": "抱歉，处理回答时出现错误。请稍后重试。"})
        return "", history


async def end_current_interview(history: List[List[str]]) -> str:
    """结束当前面试"""
    if not current_session["id"]:
        return "没有正在进行的面试"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/interview/end/{current_session['id']}"
            )
            result = response.json()

            summary = f"""
面试总结:
- 总分: {result.get('overall_score', 'N/A')}
- 优势:
{chr(10).join(['  * ' + s for s in result.get('strengths', ['未提供'])])}
- 需要改进:
{chr(10).join(['  * ' + s for s in result.get('areas_for_improvement', ['未提供'])])}
- 总结: {result.get('summary', '未提供总结')}
            """

            current_session["id"] = None

            return summary
    except Exception as e:
        print(f"Error ending interview: {e}")
        return "面试结束时出现错误。请稍后重试。"


async def analyze_code(code: str, language: str) -> str:
    """分析代码"""
    if not code.strip():
        return "请输入要分析的代码。"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/code/analyze",
                json={"code": code, "language": language},
                timeout=30.0
            )

            # 确保响应是 JSON 格式
            try:
                result = response.json()
            except json.JSONDecodeError:
                return "服务器返回了无效的响应格式。"

            # 提供默认值避免 KeyError
            complexity = result.get('complexity', {})
            best_practices = result.get('best_practices', [])
            potential_issues = result.get('potential_issues', [])
            suggestions = result.get('suggestions', [])

            return f"""
代码分析结果:

1. 复杂度:
- 时间复杂度: {complexity.get('time_complexity', '未知')}
- 空间复杂度: {complexity.get('space_complexity', '未知')}

2. 最佳实践:
{chr(10).join(['- ' + str(bp) for bp in best_practices]) if best_practices else '- 未提供最佳实践建议'}

3. 潜在问题:
{chr(10).join(['- ' + str(issue) for issue in potential_issues]) if potential_issues else '- 未发现明显问题'}

4. 改进建议:
{chr(10).join(['- ' + str(sugg) for sugg in suggestions]) if suggestions else '- 未提供改进建议'}
"""
    except httpx.TimeoutException:
        return "请求超时，请稍后重试。"
    except httpx.RequestError:
        return "无法连接到服务器，请检查网络连接。"
    except Exception as e:
        print(f"Error analyzing code: {e}")
        return f"代码分析出现错误: {str(e)}"


def create_gradio_app():
    """创建Gradio应用界面"""

    with gr.Blocks(title="IT面试助手") as app:
        gr.Markdown("# IT技术面试助手")

        with gr.Tab("面试模拟"):
            with gr.Row():
                position_level = gr.Dropdown(
                    choices=["初级", "中级", "高级"],
                    label="职位级别",
                    value="初级"
                )
                technologies = gr.Textbox(
                    label="技术栈 (用逗号分隔)",
                    placeholder="例如: Python, FastAPI, React",
                    value="Python"
                )

            start_btn = gr.Button("开始面试")
            chatbot = gr.Chatbot(
                label="面试对话",
                height=400,
                show_copy_button=True,
                type="messages"  # 显式设置消息类型
            )
            msg = gr.Textbox(
                label="你的回答",
                placeholder="在此输入你的回答...",
                show_label=True
            )

            with gr.Row():
                submit_btn = gr.Button("提交回答")
                end_btn = gr.Button("结束面试")

            summary = gr.Textbox(
                label="面试总结",
                lines=10,
                show_label=True
            )

        with gr.Tab("代码分析"):
            with gr.Row():
                code_input = gr.Code(
                    label="输入代码",
                    language="python",
                    lines=15  # 使用 lines 代替 height
                )
                language = gr.Dropdown(
                    choices=["python", "javascript", "java", "cpp", "go"],
                    label="编程语言",
                    value="python"
                )

            analyze_btn = gr.Button("分析代码")
            analysis_output = gr.Textbox(
                label="分析结果",
                lines=10,
                show_label=True
            )

        # 事件处理
        start_btn.click(
            start_new_interview,
            inputs=[position_level, technologies],
            outputs=chatbot
        )

        submit_btn.click(
            submit_answer,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

        msg.submit(
            submit_answer,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

        end_btn.click(
            end_current_interview,
            inputs=[chatbot],
            outputs=summary
        )

        analyze_btn.click(
            analyze_code,
            inputs=[code_input, language],
            outputs=analysis_output
        )

    return app


if __name__ == "__main__":
    app = create_gradio_app()
    app.launch()