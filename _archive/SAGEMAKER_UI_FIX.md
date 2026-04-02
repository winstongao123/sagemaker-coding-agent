# SageMaker UI Drifting Fix

**Status: WORKING** ✅
**Version: 2.0.0**
**Tested: January 2025**

---

## Problem

AWS SageMaker's JupyterLab has a bug where `ipywidgets.Output()` widget content escapes its container bounds. When messages are added to the chat, they push the input box and buttons down the page instead of scrolling within the designated area.

**Symptoms:**
- Chat messages appear below the buttons/input area
- UI elements drift down as more messages are added
- `height`, `max-height`, `overflow-y` properties are ignored
- Layout becomes unusable after a few messages

**Environment affected:**
- AWS SageMaker Studio / SageMaker Notebooks
- Does NOT affect Google Colab (works fine there)

## Root Cause

SageMaker's JupyterLab renders `widgets.Output()` with nested divs that don't respect the widget's layout constraints. The CSS `overflow` and `height` properties set on the widget are overridden or ignored by SageMaker's internal styling.

## Solution That Works

**Use `widgets.HTML()` with a scrollable `<div>` INSIDE the HTML content itself.**

The browser handles the scrolling, not Jupyter widgets. SageMaker can't break what it doesn't control.

### Implementation

```python
# Instead of:
# chat_output = widgets.Output(layout=widgets.Layout(height='400px', overflow_y='auto'))

# Use:
chat_display = widgets.HTML(value='')
ui_state["messages"] = []  # Store messages as tuples

def render_chat():
    """Render all messages into HTML widget with internal scroll."""
    dark = ui_state["dark_mode"]
    bg = '#1e1e1e' if dark else '#ffffff'
    fg = '#e0e0e0' if dark else '#333'
    border = '#444' if dark else '#ccc'

    msgs_html = []
    for role, content, tool_name, ts in ui_state["messages"]:
        c = escape_html(content).replace('\n', '<br>')  # Convert newlines
        if role == 'user':
            msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #26c6da;padding-left:10px;">'
                           f'<b style="color:#26c6da;">[{ts}] You:</b>'
                           f'<div style="color:{fg};margin-top:4px;">{c}</div></div>')
        elif role == 'assistant':
            msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #42a5f5;padding-left:10px;">'
                           f'<b style="color:#42a5f5;">[{ts}] Agent:</b>'
                           f'<div style="color:{fg};margin-top:4px;">{c}</div></div>')
        # ... other roles

    content = ''.join(msgs_html) or '<p style="text-align:center;">Type a message to start.</p>'

    # KEY: Scrollable div INSIDE the HTML content
    chat_display.value = f'''<div style="
        height: 400px;
        max-height: 400px;
        overflow-y: auto;
        overflow-x: hidden;
        border: 1px solid {border};
        background: {bg};
        padding: 10px;
    ">{content}</div>'''

def add_message(role, content, tool_name=None):
    """Add message and re-render."""
    ts = datetime.now().strftime('%H:%M:%S')
    ui_state["messages"].append((role, content, tool_name, ts))
    render_chat()
```

### Key Points

1. **Store messages as data** - Keep messages in a list, not displayed directly
2. **Re-render on each message** - Rebuild entire HTML on every update
3. **Scroll div inside HTML** - The `<div style="height:400px;overflow-y:auto;">` is INSIDE the HTML content
4. **Theme support** - Re-render on dark mode toggle to update all colors

### VBox Layout

```python
ui = widgets.VBox([
    header,
    row1,
    row2,
    chat_display,  # HTML widget, not Output widget
    approval_box,
    input_box,
    row3,
    tokens_html
])
```

## Approaches That FAILED

| Approach | Why It Failed |
|----------|---------------|
| `widgets.Output()` with `height='400px', overflow_y='auto'` | Content escapes bounds in SageMaker |
| `widgets.Output()` with `min_height`, `max_height` | Still ignored |
| `widgets.Box()` wrapper with `overflow='hidden'` | Blocks scrolling entirely |
| VBox with fixed height and `overflow='hidden'` | Content still escapes |
| CSS injection targeting `.widget-output`, `.jp-OutputArea` | Ignored by SageMaker |
| `widgets.HTML()` widget with layout height constraints | Widget height respected but content overflows |

## Why Google Colab Works

Colab's Jupyter implementation properly respects `widgets.Output()` layout constraints. The same code that fails in SageMaker works perfectly in Colab.

## Files Modified

- `compact/sagemaker_agent.py` - AWS Bedrock version with HTML widget fix
- `compact_GCP/gemini_agent.py` - GCP version (works without fix, but can use same approach)

## Testing

1. Run `create_chat_ui()` in SageMaker notebook
2. Send multiple messages
3. Verify:
   - Messages stay within the chat box
   - Input box and buttons stay fixed
   - Chat area scrolls internally
   - Dark mode toggle updates all message colors

## Additional Fixes

### Auto-Scroll to Bottom

When using HTML widget, scroll position resets on every update. JavaScript doesn't work in Jupyter (blocked for security). Use CSS `flex-direction: column-reverse` instead:

```python
chat_display.value = f'''<div style="height:400px;overflow-y:auto;display:flex;flex-direction:column-reverse;">
    <div style="padding:10px;">
        {content}
    </div>
</div>'''
```

This makes the container show content from the "bottom" - new messages stay visible without any JavaScript.

### Session Storage Path

Sessions are stored in `./sessions` relative to the notebook. To avoid confusion, use absolute paths:

```python
sessions_dir: str = os.path.join(os.getcwd(), "sessions")
```

The header shows session count so users know if sessions are being found.

## Summary of Working Solution

1. **Use `widgets.HTML()` instead of `widgets.Output()`**
2. **Put scrollable div INSIDE the HTML content**
3. **Use `flex-direction: column-reverse` for auto-scroll to bottom**
4. **Store messages in list, re-render entire HTML on each update**
5. **Use absolute paths for session storage**

## Files

- `compact/sagemaker_agent.py` - Version 2.0.0 with fix
- `compact_GCP/gemini_agent.py` - GCP version (works in Colab without fix)
- `complete/` - Notebook version (needs same fix applied)

## Date

Fix implemented and tested: January 2025
