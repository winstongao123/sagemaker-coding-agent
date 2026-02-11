"""
Minimal UI test - Run this in Jupyter/SageMaker to test layout fix.

Usage:
    from test_ui import test_ui
    test_ui()
"""

def test_ui():
    """Simple test UI to verify layout works."""
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output

    clear_output(wait=True)

    # Chat output - fixed height, scrollable
    chat_output = widgets.Output(layout=widgets.Layout(
        height='300px',
        min_height='300px',
        max_height='300px',
        overflow_y='scroll',
        overflow_x='hidden',
        border='1px solid #444',
        padding='5px',
        background='#1e1e1e'
    ))

    # Input - fixed height
    input_box = widgets.Textarea(
        placeholder='Type message...',
        layout=widgets.Layout(width='100%', height='60px')
    )

    # Buttons
    send_btn = widgets.Button(description='Send', button_style='primary')
    clear_btn = widgets.Button(description='Clear', button_style='warning')
    status = widgets.HTML('<span style="color:#4caf50">● Ready</span>')

    # Token display
    tokens = widgets.HTML('<span style="color:#888">Tokens: 0</span>')

    def add_msg(text, role='user'):
        color = '#26c6da' if role == 'user' else '#42a5f5'
        with chat_output:
            display(HTML(f'''
            <div style="padding:8px;margin:4px 0;border-left:3px solid {color};">
                <b style="color:{color}">{role}:</b>
                <pre style="color:#e0e0e0;margin:4px 0;white-space:pre-wrap;">{text}</pre>
            </div>
            '''))

    def on_send(b):
        msg = input_box.value.strip()
        if msg:
            add_msg(msg, 'user')
            add_msg(f'Echo: {msg}', 'agent')
            input_box.value = ''

    def on_clear(b):
        chat_output.clear_output()
        with chat_output:
            display(HTML('<p style="color:#888;text-align:center;padding:20px;">Cleared</p>'))

    send_btn.on_click(on_send)
    clear_btn.on_click(on_clear)

    # Layout - simple VBox, no special settings
    ui = widgets.VBox([
        widgets.HTML('<h3 style="color:#4a9eff;margin:0 0 10px 0;">UI Test</h3>'),
        chat_output,
        input_box,
        widgets.HBox([send_btn, clear_btn, status]),
        tokens
    ])

    # Initial message
    with chat_output:
        display(HTML('''
        <div style="color:#e0e0e0;padding:20px;text-align:center;">
            <p>Test the layout:</p>
            <ol style="text-align:left;display:inline-block;">
                <li>Type messages - they should stay in the gray box</li>
                <li>Input box and buttons should NOT move</li>
                <li>Only the message area should scroll</li>
            </ol>
        </div>
        '''))

    display(ui)
    print("UI displayed. Test by sending messages.")


if __name__ == "__main__":
    print("Run in Jupyter: from test_ui import test_ui; test_ui()")
