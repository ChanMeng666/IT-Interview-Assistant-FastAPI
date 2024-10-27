import gradio as gr
from src.ui.gradio_app import create_gradio_app

if __name__ == "__main__":
    demo = create_gradio_app()
    demo.launch(server_name="0.0.0.0", server_port=7860)