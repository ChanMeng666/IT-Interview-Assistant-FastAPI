import gradio as gr
import httpx
from typing import Dict, List
import json

# API端点配置
API_BASE_URL = "http://localhost:8000/api"

# 当前会话状态
current_session = {"id": None, "context": []}


async def create_candidate(name: str, experience: float, education: str, level: str, skills: str) -> str:
    """创建新的候选人档案"""
    try:
        # 解析技能列表
        skills_list = [s.strip() for s in skills.split(",")]
        skills_dict = {skill: "intermediate" for skill in skills_list}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/candidates/create",
                json={
                    "name": name,
                    "years_of_experience": float(experience),
                    "education": education,
                    "current_level": level,
                    "skills": skills_dict
                }
            )
            result = response.json()
            return f"候选人档案创建成功。ID: {result['candidate_id']}"
    except Exception as e:
        return f"创建候选人档案失败: {str(e)}"


async def start_interview_with_candidate(
        candidate_id: str,
        position_level: str,
        technologies: str
) -> List[Dict]:
    """使用候选人信息开始面试"""
    try:
        if not candidate_id.strip():
            return [{"role": "assistant", "content": "请输入候选人ID"}]

        tech_list = [t.strip() for t in technologies.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/interview/start",
                json={
                    "candidate_id": candidate_id,
                    "position_level": position_level,
                    "technologies": tech_list
                },
                timeout=30.0  # 增加超时时间
            )

            if response.status_code != 200:
                error_detail = response.json().get('detail', '未知错误')
                return [{"role": "assistant", "content": f"启动面试失败: {error_detail}"}]

            result = response.json()

            # 验证响应中包含必需的字段
            if not all(key in result for key in ["session_id", "question", "difficulty_level"]):
                return [{"role": "assistant", "content": "服务器返回的数据格式不正确"}]

            # 更新当前会话
            current_session["id"] = result["session_id"]

            # 添加难度信息到问题
            question_with_info = (
                f"当前难度级别: {result['difficulty_level']:.1f}/2.5\n\n"
                f"问题: {result['question']}"
            )

            return [{"role": "assistant", "content": question_with_info}]

    except httpx.TimeoutError:
        return [{"role": "assistant", "content": "请求超时，请重试"}]
    except httpx.RequestError as e:
        return [{"role": "assistant", "content": f"网络请求错误: {str(e)}"}]
    except Exception as e:
        print(f"Error in start_interview_with_candidate: {e}")
        return [{"role": "assistant", "content": f"启动面试时发生错误: {str(e)}"}]


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
    """提交答案并获取带有评估的下一个问题"""
    try:
        if not current_session["id"]:
            return "", history + [
                {"role": "user", "content": answer},
                {"role": "assistant", "content": "请先开始面试"}
            ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/interview/answer/{current_session['id']}",
                json={"answer": answer}
            )
            result = response.json()

            # 格式化评估结果
            evaluation = result["evaluation"]
            evaluation_text = f"""
评分: {evaluation['score']}/100
表现优势:
{chr(10).join(['- ' + s for s in evaluation['strength_points']])}

需要改进:
{chr(10).join(['- ' + w for w in evaluation['weakness_points']])}

沟通清晰度: {evaluation['clarity_score']}/100

当前难度级别: {result['current_difficulty']:.1f}/2.5

下一个问题:
{result['next_question']}
"""

            # 更新历史记录
            history = history or []
            history.append({"role": "user", "content": answer})
            history.append({"role": "assistant", "content": evaluation_text})

            return "", history
    except Exception as e:
        history = history or []
        history.append({"role": "user", "content": answer})
        history.append({"role": "assistant", "content": f"处理答案时出错: {str(e)}"})
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


async def explain_concept(concept: str, level: str) -> str:
    """请求概念解释"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/explain/concept",
                json={"concept": concept, "level": level}
            )
            result = response.json()

            # 格式化输出
            explanation = f"""
概念: {result.get('concept', concept)}

定义:
{result.get('definition', 'No definition available')}

关键点:
{chr(10).join(['- ' + p for p in result.get('key_points', [])])}

实际应用:
{chr(10).join(['- ' + a for a in result.get('real_world_applications', [])])}

相关概念:
{chr(10).join(['- ' + c for c in result.get('related_concepts', [])])}

学习资源:
{chr(10).join(['- ' + r for r in result.get('learning_resources', [])])}
"""
            return explanation
    except Exception as e:
        return f"获取解释时出错: {str(e)}"


async def get_learning_path(topic: str, current_level: str, target_level: str) -> str:
    """请求学习路径"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/explain/learning-path",
                json={
                    "topic": topic,
                    "current_level": current_level,
                    "target_level": target_level
                }
            )
            result = response.json()

            # 格式化输出
            path = f"""
学习路径: {topic}

预备知识:
{chr(10).join(['- ' + p for p in result.get('prerequisites', [])])}

学习阶段:
"""
            for stage in result.get('learning_stages', []):
                path += f"""
{stage['stage']}:
- 主题: {', '.join(stage['topics'])}
- 预计时间: {stage['estimated_duration']}
- 推荐资源: {', '.join(stage['resources'])}
- 实践项目: {', '.join(stage['projects'])}
"""

            path += f"""
里程碑:
{chr(10).join(['- ' + m for m in result.get('milestones', [])])}

后续步骤:
{chr(10).join(['- ' + s for s in result.get('next_steps', [])])}
"""
            return path
    except Exception as e:
        return f"获取学习路径时出错: {str(e)}"





def create_gradio_app():
    """创建Gradio应用界面"""

    with gr.Blocks(title="IT面试助手") as app:
        gr.Markdown("# IT技术面试助手")

        with gr.Tab("候选人信息"):
            with gr.Row():
                name_input = gr.Textbox(
                    label="姓名",
                    placeholder="输入候选人姓名..."
                )
                experience_input = gr.Number(
                    label="工作年限",
                    value=0
                )

            with gr.Row():
                education_input = gr.Textbox(
                    label="教育背景",
                    placeholder="最高学历..."
                )
                level_input = gr.Dropdown(
                    choices=["junior", "intermediate", "senior"],
                    label="当前级别",
                    value="junior"
                )

            skills_input = gr.Textbox(
                label="技术技能 (用逗号分隔)",
                placeholder="Python, Java, SQL..."
            )

            create_candidate_btn = gr.Button("创建候选人档案")
            candidate_result = gr.Textbox(
                label="创建结果",
                lines=2
            )


        with gr.Tab("面试模拟"):
            with gr.Row():

                candidate_id_input = gr.Textbox(
                    label="候选人ID",
                    placeholder="输入候选人ID..."
                )

                position_level = gr.Dropdown(
                    choices=["junior", "intermediate", "senior"],
                    label="面试职位级别",
                    value="junior"
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

        with gr.Tab("技术讲解"):
            with gr.Row():
                concept_input = gr.Textbox(
                    label="技术概念",
                    placeholder="输入要了解的技术概念..."
                )
                level_select = gr.Dropdown(
                    choices=["beginner", "intermediate", "advanced"],
                    label="讲解深度",
                    value="intermediate"
                )

            explain_btn = gr.Button("获取解释")
            explanation_output = gr.Textbox(
                label="概念解释",
                lines=10,
                show_label=True
            )

            gr.Markdown("---")

            with gr.Row():
                topic_input = gr.Textbox(
                    label="学习主题",
                    placeholder="输入要学习的技术主题..."
                )
                current_level = gr.Dropdown(
                    choices=["beginner", "intermediate", "advanced"],
                    label="当前水平",
                    value="beginner"
                )
                target_level = gr.Dropdown(
                    choices=["intermediate", "advanced", "expert"],
                    label="目标水平",
                    value="intermediate"
                )

            path_btn = gr.Button("生成学习路径")
            path_output = gr.Textbox(
                label="学习路径建议",
                lines=15,
                show_label=True
            )


        # 事件处理
        create_candidate_btn.click(
            create_candidate,
            inputs=[
                name_input,
                experience_input,
                education_input,
                level_input,
                skills_input
            ],
            outputs=candidate_result
        )

        start_btn.click(
            start_interview_with_candidate,
            inputs=[
                candidate_id_input,
                position_level,
                technologies
            ],
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

        explain_btn.click(
            explain_concept,
            inputs=[concept_input, level_select],
            outputs=explanation_output
        )

        path_btn.click(
            get_learning_path,
            inputs=[topic_input, current_level, target_level],
            outputs=path_output
        )

    return app


if __name__ == "__main__":
    app = create_gradio_app()
    app.launch()