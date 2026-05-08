# v4 create_chat_ui extract (read-only reference for v5 phase_2 investigation)
# Source: compact_v4/MAIN/agent/sagemaker_agent.py:9735-12088

def create_chat_ui(mock_mode: bool = None):
    """Create and display the chat interface in Jupyter."""
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output

    # Clear any previous UI to prevent duplicates
    clear_output(wait=True)

    # Override mock mode if specified
    if mock_mode is not None:
        CONFIG.mock_mode = mock_mode

    # Create client
    client = BedrockClient(CONFIG.model_id, CONFIG.region, CONFIG.mock_mode)

    # UI state
    ui_state = {
        "dark_mode": True,  # Default dark mode like GCP
        "client": client,
        "agent": None,
        "session": None,
        "lock": False,
        "stop_requested": False,  # For stop button
        "authenticated": not CONFIG.require_auth,
        "model_connection_ok": None,  # True/False/None(unknown)
        "model_connection_msg": "Not validated yet",
        "active_skills": [],
        "deactivated_skills": set(),  # V4.9.1: skills explicitly turned off via /unskill or /skill clear — auto-match skips them for the session
        "session_phase": "",  # Current work phase, shown in status bar. Set via /phase <text>.
        "chat_height": 500,  # V4.8.0: default chat height in px (adjustable via slider)
    }
    ui_state["model_change_lock"] = False

    # NEW APPROACH: HTML widget with scrollable div inside
    # Browser handles scrolling, not Jupyter widgets
    ui_state["messages"] = []  # Store message tuples: (role, content, tool_name, timestamp)
    ui_state["todos"] = []  # Store todos for persistence (synced with global _TODOS)

    chat_display = widgets.HTML(value='')  # Will be updated by render_chat()
    todo_display = widgets.HTML(value='')  # Todo list display

    def _format_inline_md(text: str, dark: bool) -> str:
        """Render a safe subset of inline markdown."""
        s = escape_html(text)
        code_bg = "#2b2b2b" if dark else "#f3f4f6"
        code_fg = "#e06c75" if dark else "#c7254e"
        bold_fg = "#ffffff" if dark else "#000000"
        s = re.sub(r"`([^`]+)`", rf'<code style="background:{code_bg};color:{code_fg};padding:1px 5px;border-radius:3px;font-size:0.9em;">\1</code>', s)
        s = re.sub(r"\*\*\*([^*]+)\*\*\*", rf'<b style="color:{bold_fg};"><i>\1</i></b>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", rf'<b style="color:{bold_fg};">\1</b>', s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        return s

    def _render_assistant_markdown(text: str, fg: str, dark: bool) -> str:
        """Render common markdown blocks (tables/lists/code/headers) into HTML."""
        text = str(text)
        lines = text.splitlines()
        chart_bg = "#171717" if dark else "#f6f8fa"

        def _has_markdown_table(ls: List[str]) -> bool:
            for j in range(len(ls) - 1):
                if ls[j].strip().startswith("|") and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", ls[j + 1]):
                    return True
            return False

        def _looks_ascii_art(ls: List[str]) -> bool:
            non_empty = [ln for ln in ls if ln.strip()]
            if len(non_empty) < 3:
                return False
            score = 0
            for ln in non_empty:
                s = ln.rstrip()
                if len(s) - len(s.lstrip()) >= 2:
                    score += 1
                if re.search(r"\+\-[-+]+", s):
                    score += 2
                if re.search(r"^\s*[\d.]+\s*\|", s):
                    score += 2
                if "|" in s:
                    score += 1
                if re.search(r"[xXoO]{2,}", s) and not re.search(r"\*\*|\#\#", s):
                    score += 1
            return score >= 6

        # V4.3.3 fix: Removed early-return unicode check that wrapped ENTIRE response
        # in <pre> when any box-drawing char appeared. Charts inside ``` code fences
        # are handled by the code block parser below. Charts outside fences go through
        # the line-by-line parser which handles them correctly.
        if _looks_ascii_art(lines) and not _has_markdown_table(lines) and not any(re.search(r"\*\*|##", l) for l in lines):
            return (
                f'<pre style="background:{chart_bg};color:{fg};padding:8px;border-radius:6px;overflow:auto;'
                f'white-space:pre;line-height:1.3;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;">'
                f'{escape_html(text)}</pre>'
            )

        out = []
        i = 0
        code_bg = "#171717" if dark else "#f6f8fa"
        table_border = "#444" if dark else "#d0d7de"

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("```"):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                code_fg = "#abb2bf" if dark else "#383a42"
                code_border = "#333" if dark else "#d0d7de"
                out.append(
                    f'<pre style="background:{code_bg};color:{code_fg};padding:12px;border-radius:6px;'
                    f'border:1px solid {code_border};overflow:auto;font-size:12px;line-height:1.5;'
                    f'font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;margin:8px 0;">'
                    f'{escape_html(chr(10).join(code_lines))}</pre>'
                )
                i += 1
                continue

            if stripped.startswith("|") and (i + 1) < len(lines) and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", lines[i + 1]):
                headers = [escape_html(c.strip()) for c in stripped.strip("|").split("|")]
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cols = [escape_html(c.strip()) for c in lines[i].strip().strip("|").split("|")]
                    rows.append(cols)
                    i += 1
                head_html = "".join([f'<th style="text-align:left;padding:6px;border:1px solid {table_border};">{h}</th>' for h in headers])
                body_html = []
                for row in rows:
                    cells = "".join([f'<td style="padding:6px;border:1px solid {table_border};">{c}</td>' for c in row])
                    body_html.append(f"<tr>{cells}</tr>")
                out.append(
                    f'<table style="border-collapse:collapse;margin:8px 0;color:{fg};">'
                    f"<thead><tr>{head_html}</tr></thead><tbody>{''.join(body_html)}</tbody></table>"
                )
                continue

            if stripped.startswith("- ") or stripped.startswith("* "):
                items = []
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith("- ") or s.startswith("* "):
                        items.append(_format_inline_md(s[2:].strip(), dark))
                        i += 1
                    else:
                        break
                out.append("<ul style=\"margin:8px 0 8px 20px;line-height:1.6;\">" + "".join([f"<li style=\"margin:2px 0;\">{x}</li>" for x in items]) + "</ul>")
                continue

            # Numbered lists (1. 2. 3.)
            _ol_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            if _ol_match:
                items = []
                while i < len(lines):
                    s = lines[i].strip()
                    _nm = re.match(r"^(\d+)\.\s+(.*)$", s)
                    if _nm:
                        items.append(_format_inline_md(_nm.group(2).strip(), dark))
                        i += 1
                    else:
                        break
                out.append("<ol style=\"margin:8px 0 8px 20px;line-height:1.6;\">" + "".join([f"<li style=\"margin:2px 0;\">{x}</li>" for x in items]) + "</ol>")
                continue

            m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                text_part = _format_inline_md(m.group(2), dark)
                accent = "#4a9eff" if dark else "#1a56db"
                if level == 1:
                    out.append(f'<div style="font-weight:800;font-size:20px;margin:16px 0 8px 0;color:{accent};border-bottom:1px solid {"#333" if dark else "#ddd"};padding-bottom:4px;">{text_part}</div>')
                elif level == 2:
                    out.append(f'<div style="font-weight:700;font-size:16px;margin:14px 0 6px 0;color:{accent};">{text_part}</div>')
                else:
                    out.append(f'<div style="font-weight:600;font-size:14px;margin:10px 0 4px 0;color:{fg};">{text_part}</div>')
                i += 1
                continue

            if stripped:
                out.append(f'<div style="margin:3px 0;color:{fg};line-height:1.5;">{_format_inline_md(line, dark)}</div>')
            else:
                out.append("<div style=\"height:8px;\"></div>")
            i += 1

        return "".join(out)

    def render_chat():
        """Render all messages into the HTML widget with internal scroll."""
        dark = ui_state["dark_mode"]
        bg = '#1e1e1e' if dark else '#ffffff'
        fg = '#e0e0e0' if dark else '#333'
        border = '#444' if dark else '#ccc'

        msgs_html = []
        for role, content, tool_name, ts in ui_state["messages"]:
            raw = str(content)
            c = escape_html(raw).replace('\n', '<br>')
            if role == 'user':
                msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #26c6da;padding-left:10px;"><b style="color:#26c6da;">[{ts}] You:</b><div style="color:{fg};margin-top:4px;">{c}</div></div>')
            elif role == 'assistant':
                rendered = _render_assistant_markdown(raw, fg, dark)
                msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #42a5f5;padding-left:10px;"><b style="color:#42a5f5;">[{ts}] Agent:</b><div style="color:{fg};margin-top:4px;">{rendered}</div></div>')
            elif role == 'tool':
                icon = TOOL_ICONS.get(tool_name, '🔧') if tool_name else '🔧'
                tool_label = escape_html(tool_name or "Tool")
                # Check for inline images (base64-encoded charts/images)
                inline_match = re.search(r'\[INLINE_IMAGE:([A-Za-z0-9+/=]+)\]', raw)
                if inline_match:
                    img_b64 = inline_match.group(1)
                    text_part = escape_html(raw[:inline_match.start()].strip()).replace('\n', '<br>')
                    img_html = f'<div style="margin:4px 0;">{text_part}</div><img src="data:image/png;base64,{img_b64}" style="max-width:100%;border-radius:4px;margin:4px 0;" />'
                    msgs_html.append(f'<details open style="margin:5px 0;border-left:3px solid #ffa726;padding-left:10px;"><summary style="color:#ffa726;cursor:pointer;">{icon} {tool_label}</summary>{img_html}</details>')
                else:
                    msgs_html.append(f'<details style="margin:5px 0;border-left:3px solid #ffa726;padding-left:10px;"><summary style="color:#ffa726;cursor:pointer;">{icon} {tool_label}</summary><pre style="color:{fg};white-space:pre-wrap;max-height:150px;overflow:auto;font-size:11px;margin:4px 0;">{c}</pre></details>')
            elif role == 'thinking':
                msgs_html.append(f'<div style="margin:5px 0;color:#ab47bc;font-size:12px;border-left:3px solid #ab47bc;padding-left:10px;">💭 {c[:300]}...</div>')
            elif role == 'system':
                msgs_html.append(f'<div style="margin:5px 0;color:#ef5350;border-left:3px solid #ef5350;padding-left:10px;">⚠️ {c}</div>')
            else:
                msgs_html.append(f'<div style="color:{fg};">{c}</div>')

        content = ''.join(msgs_html) if msgs_html else f'<p style="color:{fg};text-align:center;padding:20px;">Type a message below to start.</p>'

        # CSS-only auto-scroll: use flex-direction: column-reverse
        # Messages are wrapped in inner div, outer div is reversed flex container
        # This makes new content appear at bottom and stay visible
        # V4.8.0: resizable chat window (resize:vertical) — user can drag bottom edge to enlarge
        _chat_h = ui_state.get("chat_height", 500)  # Default 500px, adjustable via height slider
        chat_display.value = f'''<div style="height:{_chat_h}px;min-height:200px;max-height:90vh;overflow-y:auto;overflow-x:hidden;border:1px solid {border};background:{bg};display:flex;flex-direction:column-reverse;width:100%;box-sizing:border-box;resize:vertical;">
            <div style="padding:10px;font-family:system-ui,-apple-system,sans-serif;">
                {content}
            </div>
        </div>'''

    def render_todos():
        """Render todos in a collapsible panel (2-stage)."""
        dark = ui_state["dark_mode"]
        bg = '#2d2d2d' if dark else '#f5f5f5'
        fg = '#e0e0e0' if dark else '#333'
        border = '#444' if dark else '#ccc'

        if not ui_state["todos"]:
            todo_display.value = ''
            return

        todos_html = []
        for t in ui_state["todos"]:
            status = t.get("status", "pending")
            content = t.get("content", "Unknown")
            if status == "completed":
                icon, color = "✅", "#4caf50"
            elif status == "in_progress":
                icon, color = "🔄", "#ff9800"
            else:
                icon, color = "⬜", "#888"
            todos_html.append(f'<div style="padding:2px 0;color:{color};font-size:12px;">{icon} {content}</div>')

        todo_display.value = f'''<details style="background:{bg};border:1px solid {border};border-radius:5px;padding:5px 10px;margin-bottom:5px;">
            <summary style="cursor:pointer;color:{fg};font-weight:bold;font-size:12px;">📋 Todos ({len([t for t in ui_state["todos"] if t.get("status") != "completed"])}/{len(ui_state["todos"])})</summary>
            <div style="margin-top:5px;">{''.join(todos_html)}</div>
        </details>'''

        # Sync global _TODOS
        global _TODOS
        _TODOS = ui_state["todos"]

    def sync_todos_from_global():
        """Sync global _TODOS to ui_state (called after tool_todo_write)."""
        global _TODOS
        ui_state["todos"] = _TODOS.copy() if _TODOS else []
        render_todos()

    # Set global callback for tool_todo_write to update UI
    global _TODO_UI_SYNC
    _TODO_UI_SYNC = sync_todos_from_global

    input_box = widgets.Textarea(placeholder='Type your message...', layout=widgets.Layout(
        width='100%', height='80px'
    ))
    send_btn = widgets.Button(description='Send', button_style='primary', icon='paper-plane')
    stop_btn = widgets.Button(description='Stop', button_style='danger', icon='stop', layout=widgets.Layout(display='none'))
    clear_btn = widgets.Button(description='Clear', button_style='warning', icon='trash')
    save_btn = widgets.Button(description='Save', button_style='info', icon='save')
    compact_btn = widgets.Button(description='Compact', button_style='', icon='compress', tooltip='Compress context by summarizing conversation')
    cleanup_btn = widgets.Button(description='🧹 Clean', button_style='', icon='eraser', tooltip='Delete all local traces (sessions, audit, snapshots, index)')
    status_html = widgets.HTML(value='<span style="color:#4caf50"><b>● Ready</b></span>')
    mode_html = widgets.HTML(value='')
    tokens_html = widgets.HTML(value='<span style="color:gray;font-size:11px;">Tokens: 0</span>')

    # Plan Mode checkbox (read-only mode — agent can only read/explore, no writes)
    plan_mode_toggle = widgets.Checkbox(
        value=False,
        description='Plan Mode',
        indent=False,
        tooltip='When ON: Agent only reads/explores, no file writes. When OFF: Normal execution.',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='auto')
    )

    # Auto-compact checkbox (ON by default - always auto-compact at 90%)
    auto_compact_checkbox = widgets.Checkbox(
        value=True,
        description='Auto-Compact',
        indent=False,
        tooltip='Automatically compact when context exceeds 90%',
        layout=widgets.Layout(width='auto')
    )

    # Approval dialog
    approval_output = widgets.Output()
    approve_btn = widgets.Button(description='Approve', button_style='success', icon='check')
    approve_always_btn = widgets.Button(description='Always', button_style='info', icon='thumbs-up')
    deny_btn = widgets.Button(description='Deny', button_style='danger', icon='times')
    approval_box = widgets.VBox([approval_output, widgets.HBox([approve_btn, approve_always_btn, deny_btn])])
    approval_box.layout.display = 'none'

    # Ask-user dialog (text input for agent questions)
    ask_user_output = widgets.Output()
    ask_user_input = widgets.Text(placeholder='Type your answer...', layout=widgets.Layout(width='80%'))
    ask_user_submit = widgets.Button(description='Submit', button_style='success', icon='check')
    ask_user_skip = widgets.Button(description='Skip', button_style='warning', icon='forward')
    ask_user_box = widgets.VBox([ask_user_output, widgets.HBox([ask_user_input, ask_user_submit, ask_user_skip])])
    ask_user_box.layout.display = 'none'
    pending_user_input = {"result": None, "event": None}

    # Model selector - default is whatever CONFIG.model_id resolves to (Sonnet 4.5
    # since v4.10.1, was Haiku 4.5 prior). Falls back to BEDROCK_MODELS[0] if the
    # configured ARN is missing from the dropdown options.
    model_values = [m[1] for m in BEDROCK_MODELS]
    default_model = CONFIG.model_id if CONFIG.model_id in model_values else BEDROCK_MODELS[0][1]
    model_dropdown = widgets.Dropdown(
        description='Model:',
        options=BEDROCK_MODELS,
        value=default_model,
        layout=widgets.Layout(width='280px')
    )
    # Update CONFIG to match selected model
    CONFIG.model_id = default_model

    # Session selector and name input
    session_dropdown = widgets.Dropdown(description='Session:', options=[('New Session', None)], layout=widgets.Layout(width='250px'))
    session_name_input = widgets.Text(placeholder='Session name (optional)', layout=widgets.Layout(width='200px'))
    load_btn = widgets.Button(description='Load', button_style='info', icon='folder-open')
    new_btn = widgets.Button(description='New', button_style='success', icon='plus')

    # Session budget slider (live control)
    # V4.8.0: Budget as editable text box (display-only metric, never stops execution)
    budget_input = widgets.BoundedFloatText(
        value=CONFIG.session_cost_limit if CONFIG.session_cost_limit > 0 else 10.0,
        min=0.0, max=999.0, step=0.5,
        description='Budget $:',
        style={'description_width': '70px'},
        layout=widgets.Layout(width='160px'),
        tooltip='Display-only cost tracking. Does NOT stop agent. Set 0 to disable warning.'
    )
    # Alias for backward compat (other code references budget_slider)
    budget_slider = budget_input
    def on_budget_change(change):
        CONFIG.session_cost_limit = change['new']
        update_mode_display()
        update_tokens_display()
    budget_input.observe(on_budget_change, names='value')
    # Initialize config
    if CONFIG.session_cost_limit <= 0:
        CONFIG.session_cost_limit = 10.0

    # Live parameter controls
    temp_slider = widgets.FloatSlider(
        value=CONFIG.temperature,
        min=0.0, max=1.0, step=0.1,
        description='Temperature:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='250px')
    )
    thinking_checkbox = widgets.Checkbox(
        value=CONFIG.thinking_enabled,
        description='Extended Thinking',
        indent=False,
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='auto')
    )
    thinking_budget_slider = widgets.IntSlider(
        value=CONFIG.thinking_budget,
        min=1024, max=16000, step=1024,
        description='Think Budget:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='250px'),
        disabled=not CONFIG.thinking_enabled
    )
    # V4.8.0: Chat height slider — user can adjust chat window size
    chat_height_slider = widgets.IntSlider(
        value=500, min=200, max=1200, step=50,
        description='Chat Height:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='250px')
    )
    def on_chat_height_change(change):
        ui_state["chat_height"] = change['new']
        render_chat()
    chat_height_slider.observe(on_chat_height_change, names='value')

    dark_mode_checkbox = widgets.Checkbox(
        value=True,  # Default on like GCP
        description='Dark Mode',
        indent=False,
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='auto')
    )
    approval_checkbox = widgets.Checkbox(
        value=CONFIG.require_tool_approval,
        description='Require Approval',
        indent=False,
        style={'description_width': 'initial'},
        tooltip='If OFF, tool calls execute without manual Approve/Deny prompt.',
        layout=widgets.Layout(width='auto')
    )

    def validate_model_connection(model_id: str) -> Tuple[bool, str]:
        """Validate the selected model is actually callable in current account/region."""
        try:
            test_client = BedrockClient(model_id, CONFIG.region, CONFIG.mock_mode)
            if CONFIG.mock_mode:
                return True, "Mock mode (no Bedrock call)"
            resp = test_client.chat(
                messages=[{"role": "user", "content": "ping"}],
                system="Reply with OK.",
                tools=None,
                max_tokens=8,
                temperature=0.0,
            )
            # Track ping cost (small but real Bedrock spend)
            if resp and resp.usage:
                TOKENS.add(resp.usage, model_id=model_id)
            return True, "Connected and available"
        except Exception as e:
            err = str(e).strip().replace("\n", " ")
            return False, err[:180] if err else "Model not available"

    # Model change handler
    def on_model_change(change):
        if ui_state.get("model_change_lock"):
            return
        new_model = change['new']
        old_model = CONFIG.model_id
        try:
            ok, conn_msg = validate_model_connection(new_model)
            if not ok:
                raise RuntimeError(conn_msg)
            new_client = BedrockClient(new_model, CONFIG.region, CONFIG.mock_mode)
            CONFIG.model_id = new_model
            ui_state["client"] = new_client
            ui_state["model_connection_ok"] = True
            ui_state["model_connection_msg"] = conn_msg
            if ui_state["agent"]:
                ui_state["agent"].client = new_client
                AUDIT.log(ui_state["agent"].session_id, "config_change", "model",
                          {"old": old_model, "new": new_model})
            add_message('system', f'Model connected: {new_model}')
            status_html.value = '<span style="color:#4caf50"><b>● Ready (model connected)</b></span>'
        except Exception as e:
            ui_state["model_change_lock"] = True
            try:
                model_dropdown.value = old_model
            finally:
                ui_state["model_change_lock"] = False
            ui_state["model_connection_ok"] = False
            ui_state["model_connection_msg"] = str(e)[:180]
            add_message('system', f'Model switch failed: {new_model}. Kept {old_model}. Error: {str(e)[:120]}')
            status_html.value = '<span style="color:#f44336"><b>● Ready (model unavailable)</b></span>'
        update_mode_display()

    def on_temp_change(change):
        CONFIG.temperature = change['new']
        update_mode_display()

    def on_thinking_change(change):
        CONFIG.thinking_enabled = change['new']
        thinking_budget_slider.disabled = not change['new']
        if change['new']:
            # Thinking requires temperature=1, show notice
            ui_state["prev_temperature"] = temp_slider.value
            temp_slider.value = 1.0
            temp_slider.disabled = True
        else:
            temp_slider.disabled = False
            if "prev_temperature" in ui_state:
                temp_slider.value = ui_state["prev_temperature"]
        update_mode_display()

    def on_budget_change(change):
        CONFIG.thinking_budget = change['new']
        update_mode_display()

    def on_dark_mode_change(change):
        ui_state["dark_mode"] = change['new']
        # Re-render chat with new colors (colors are in HTML now)
        render_chat()
        render_todos()
        # Update header
        if "header" in ui_state and ui_state["header"]:
            ui_state["header"].value = ui_state["get_header_html"]()
        # Update token display
        if "update_tokens" in ui_state:
            ui_state["update_tokens"]()
        update_mode_display()

    def on_approval_toggle(change):
        CONFIG.require_tool_approval = change['new']
        add_message('system', f'Tool approvals {"enabled" if CONFIG.require_tool_approval else "disabled"}')
        update_mode_display()

    # Sub-agent model overrides UI
    _sa_model_options = [("Same as main", "")] + list(BEDROCK_MODELS)
    _sa_types = ["explore", "review", "general", "build", "plan"]
    _sa_dropdowns = {}
    for _sa_type in _sa_types:
        _current = CONFIG.agent_overrides.get(_sa_type, {}).get("model", "")
        _sa_dropdowns[_sa_type] = widgets.Dropdown(
            description=f'{_sa_type}:',
            options=_sa_model_options,
            value=_current if _current in [m[1] for m in BEDROCK_MODELS] else "",
            layout=widgets.Layout(width='320px'),
            style={'description_width': '70px'}
        )

    def _on_sa_model_change(agent_type):
        def handler(change):
            new_val = change['new']
            if agent_type not in CONFIG.agent_overrides:
                CONFIG.agent_overrides[agent_type] = {}
            if new_val:
                CONFIG.agent_overrides[agent_type]["model"] = new_val
                label = next((n for n, v in BEDROCK_MODELS if v == new_val), new_val)
                add_message('system', f'Sub-agent `{agent_type}` model → {label}')
            else:
                CONFIG.agent_overrides[agent_type].pop("model", None)
                add_message('system', f'Sub-agent `{agent_type}` model → same as main')
        return handler

    for _sa_type in _sa_types:
        _sa_dropdowns[_sa_type].observe(_on_sa_model_change(_sa_type), names='value')

    _sa_toggle = widgets.ToggleButton(
        value=False, description='Sub-Agent Models ▶',
        button_style='', icon='cogs',
        layout=widgets.Layout(width='180px', height='28px'),
        style={'font_weight': 'normal'}
    )
    _sa_panel = widgets.VBox([_sa_dropdowns[t] for t in _sa_types])
    _sa_panel.layout.display = 'none'

    def _on_sa_toggle(change):
        if change['new']:
            _sa_panel.layout.display = 'flex'
            _sa_toggle.description = 'Sub-Agent Models ▼'
        else:
            _sa_panel.layout.display = 'none'
            _sa_toggle.description = 'Sub-Agent Models ▶'
    _sa_toggle.observe(_on_sa_toggle, names='value')

    model_dropdown.observe(on_model_change, names='value')
    temp_slider.observe(on_temp_change, names='value')
    thinking_checkbox.observe(on_thinking_change, names='value')
    thinking_budget_slider.observe(on_budget_change, names='value')
    dark_mode_checkbox.observe(on_dark_mode_change, names='value')
    approval_checkbox.observe(on_approval_toggle, names='value')
    plan_mode_toggle.observe(lambda change: update_mode_display(), names='value')

    pending_approval = {"result": None}

    def update_mode_display():
        """Render current runtime mode so users can verify active state."""
        plan = "ON" if plan_mode_toggle.value else "OFF"
        thinking = "ON" if CONFIG.thinking_enabled else "OFF"
        auth = "ON" if CONFIG.require_auth else "OFF"
        approval = "ON" if CONFIG.require_tool_approval else "OFF"
        skills_count = len(ui_state.get("active_skills", []))
        dark = ui_state.get("dark_mode", True)
        text_color = "#aab4be" if dark else "#666"
        if ui_state.get("model_connection_ok") is True:
            model_state = "Connected"
            model_color = "#4caf50"
        elif ui_state.get("model_connection_ok") is False:
            model_state = "Unavailable"
            model_color = "#f44336"
        else:
            model_state = "Unknown"
            model_color = "#ff9800"
        model_msg = escape_html(ui_state.get("model_connection_msg", "Not validated yet"))
        # MCP status
        mcp_status = MCP_MANAGER.status_summary()
        mcp_part = f' | {mcp_status}' if mcp_status else ''
        # Active skill
        active_skill_names = ", ".join(ui_state.get("active_skills", []))
        skill_part = f' | Skill: <b>{escape_html(active_skill_names)}</b>' if active_skill_names else f' | Skills: <b>{skills_count}</b>'
        # Custom commands count
        cmd_count = len(COMMANDS.commands)
        cmd_part = f' | Cmds: <b>{cmd_count}</b>' if cmd_count else ''
        # Cost tracking
        cost_str = TOKENS.get_cost()
        cost_part = f' | Cost: <b>{cost_str}</b>' if TOKENS.session_cost > 0 else ''
        # Session phase (from /phase <text>, falls back to active skill)
        phase_text = ui_state.get("session_phase", "")
        if not phase_text and active_skill_names:
            phase_text = f"skill:{active_skill_names}"
        phase_color = "#4fc3f7" if dark else "#0277bd"
        phase_part = f' | <span style="color:{phase_color}">Phase: <b>{escape_html(phase_text)}</b></span>' if phase_text else ''

        mode_html.value = (
            f'<div style="font-size:12px;color:{text_color};margin:4px 0;">'
            f'Model: <b>{escape_html(CONFIG.model_id)}</b> | '
            f'Status: <b style="color:{model_color}">{model_state}</b> '
            f'(<span>{model_msg}</span>) | '
            f'Plan: <b>{plan}</b> | '
            f'Thinking: <b>{thinking}</b> (budget {CONFIG.thinking_budget}) | '
            f'Auth: <b>{auth}</b> | '
            f'Approval: <b>{approval}</b>{skill_part}{mcp_part}{cmd_part}{cost_part}{phase_part} | '
            f'Exec: <b>{escape_html(CONFIG.execution_mode)}</b>'
            f'</div>'
        )

    def get_colors():
        """Get color scheme based on dark mode."""
        if ui_state["dark_mode"]:
            return {
                'bg': '#1e1e1e', 'fg': '#e0e0e0', 'fg_muted': '#a0a0a0',
                'border': '#444', 'bar_bg': '#333',
            }
        else:
            return {
                'bg': '#ffffff', 'fg': '#1a1a1a', 'fg_muted': '#666666',
                'border': '#ccc', 'bar_bg': '#ddd',
            }

    def update_session_list():
        sessions = SESSIONS.list_sessions()
        options = [('New Session', None)] + [(f"{s['title'][:30]} ({s['id']})", s['id']) for s in sessions[:10]]
        session_dropdown.options = options

    def update_tokens_display():
        """Update token display with cost monitor and context progress bar."""
        stats = TOKENS.get_stats()
        c = get_colors()

        # Context window estimation (message-based, consistent with auto-compact trigger)
        if ui_state["agent"] and ui_state["agent"].messages:
            ctx_tokens = CONTEXT.estimate_tokens(ui_state["agent"].messages)
        else:
            ctx_tokens = 0
        max_ctx = CONFIG.context_max_tokens
        ctx_pct = (ctx_tokens / max_ctx * 100) if max_ctx > 0 else 0

        # Color based on context usage
        if ctx_pct >= 90:
            ctx_color = "#f44336"
        elif ctx_pct >= 75:
            ctx_color = "#ff9800"
        else:
            ctx_color = "#4caf50"

        bar_width = min(ctx_pct, 100)

        # Cost formatting
        session_cost = stats["session_cost_usd"]
        last_cost = stats["last_cost_usd"]
        cost_fmt = f"${session_cost:.4f}" if session_cost < 0.01 else f"${session_cost:.2f}"
        last_fmt = f"${last_cost:.4f}" if last_cost < 0.01 else f"${last_cost:.2f}"

        # Model rate (per 1M tokens for readability)
        pricing = _MODEL_PRICING.get(CONFIG.model_id)
        if pricing:
            rate_str = f'${pricing["input"]*1000:.2f}/${pricing["output"]*1000:.2f} per 1M in/out'
        else:
            rate_str = 'pricing N/A'

        # Fixed overhead per API call (system prompt + tool schemas + Bedrock)
        overhead = TOKENS.get_fixed_overhead()
        true_ctx = ctx_tokens + overhead

        # Cache savings and original cost calculation
        cache_savings = TOKENS.get_cache_savings_usd()
        original_cost = session_cost + cache_savings  # What it WOULD have cost without caching
        if cache_savings > 0:
            cache_pct = min(100, (TOKENS.session_cache_read / TOKENS.session_input * 100)) if TOKENS.session_input > 0 else 0
            orig_fmt = f"${original_cost:.4f}" if original_cost < 0.01 else f"${original_cost:.2f}"
            save_fmt = f"${cache_savings:.4f}" if cache_savings < 0.01 else f"${cache_savings:.2f}"
            cost_line = f'💰 Actual: <b>{cost_fmt}</b> | Without cache: {orig_fmt} | Saved: <b style="color:#4caf50">{save_fmt}</b> ({cache_pct:.0f}% cached)'
        else:
            cost_line = f'💰 Cost: <b>{cost_fmt}</b> | Last: {last_fmt} | {rate_str}'
            if TOKENS.session_input > 0:
                cost_line += ' | Cache: <span style="color:#ff9800;">inactive</span>'

        # Budget bar: only shown when session_cost_limit > 0
        budget_block = ""
        budget_limit = CONFIG.session_cost_limit
        if budget_limit > 0:
            budget_pct = min(100, (session_cost / budget_limit * 100)) if budget_limit > 0 else 0
            if budget_pct >= 100:
                budget_color = "#f44336"  # red - over
            elif budget_pct >= 80:
                budget_color = "#ff9800"  # orange - warn
            else:
                budget_color = "#4caf50"  # green - ok
            budget_fmt = f"${budget_limit:.4f}" if budget_limit < 0.01 else f"${budget_limit:.2f}"
            budget_block = (
                f'<div style="margin-top:3px;">'
                f'<span style="color:{budget_color}">Budget: {budget_pct:.0f}% ({cost_fmt} / {budget_fmt})</span>'
                f'</div>'
                f'<div style="background:{c["bar_bg"]};height:4px;border-radius:2px;margin-top:2px;">'
                f'<div style="background:{budget_color};width:{min(budget_pct,100)}%;height:100%;border-radius:2px;"></div>'
                f'</div>'
            )

        # Phase line (above cost so users see current task first)
        phase_text = ui_state.get("session_phase", "")
        phase_block = ""
        if phase_text:
            phase_block = (
                f'<div style="margin-top:2px;color:#4fc3f7;">'
                f'🎯 Phase: <b>{escape_html(phase_text)}</b>'
                f'</div>'
            )

        tokens_html.value = f'''
        <div style="font-size:11px;color:{c["fg_muted"]};line-height:1.5;">
            {phase_block}
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;">
                <span>📊 In <b>{stats["session_input"]:,}</b> | Out <b>{stats["session_output"]:,}</b> | Calls {stats["api_calls"]}</span>
            </div>
            <div style="margin-top:2px;">{cost_line}</div>
            <div style="margin-top:3px;">
                <span style="color:{ctx_color}">Context: {ctx_pct:.1f}% ({ctx_tokens:,} / {max_ctx:,})</span>
            </div>
            <div style="background:{c["bar_bg"]};height:4px;border-radius:2px;margin-top:2px;">
                <div style="background:{ctx_color};width:{bar_width}%;height:100%;border-radius:2px;"></div>
            </div>
            {budget_block}
        </div>
        '''
        # Also refresh status line so cost stays in sync
        update_mode_display()

    def add_message(role: str, content: str, tool_name: str = None):
        """Add message and re-render chat."""
        ts = datetime.now().strftime('%H:%M:%S')
        ui_state["messages"].append((role, content, tool_name, ts))
        render_chat()

    # Tools where "Always" approve is too dangerous (each invocation has different risk)
    HIGH_RISK_TOOLS = {"bash", "python_exec", "task", "web_fetch"}

    def request_approval(tool_name: str, tool_input: Dict) -> bool:
        import threading
        if not CONFIG.require_tool_approval:
            return True

        # Check config-based permission rules
        if CONFIG.permission_rules:
            import fnmatch as _fnmatch
            # Direct tool-name rules
            rule = CONFIG.permission_rules.get(tool_name)
            if rule == "allow":
                return True
            if rule == "deny":
                add_message('system', f'Denied by permission rule: {tool_name}')
                return False
            # Check pattern-based rules: "tool:pattern" (e.g. "bash:docker*")
            # and file-pattern rules (e.g. "*.env", "**/*.key")
            target = tool_input.get("file_path") or tool_input.get("filepath") or tool_input.get("path")
            command = tool_input.get("command", "")
            for pattern, action in CONFIG.permission_rules.items():
                # tool:command_pattern rules (e.g., "bash:rm*", "bash:docker*")
                if ":" in pattern and not pattern.startswith("*"):
                    rule_tool, rule_pattern = pattern.split(":", 1)
                    if rule_tool == tool_name and command and _fnmatch.fnmatch(str(command), rule_pattern):
                        if action == "deny":
                            add_message('system', f'Denied by pattern rule: {pattern}')
                            return False
                        if action == "allow":
                            return True
                # File-pattern rules (e.g., "*.env", "**/secrets/*")
                elif pattern.startswith("*") or "/" in pattern:
                    if target and _fnmatch.fnmatch(str(target), pattern):
                        if action == "deny":
                            add_message('system', f'Denied by pattern rule: {pattern}')
                            return False
                        if action == "allow":
                            return True
        # "Always" only works for low-risk tools (file creation, etc.)
        # bash and python_exec require per-invocation approval since args vary wildly
        if tool_name not in HIGH_RISK_TOOLS and tool_name in ui_state.get("always_allow", set()):
            add_message('system', f'[OK] Auto-approved: {tool_name}')
            return True
        pending_approval["result"] = None
        pending_approval["tool_name"] = tool_name
        approval_event = threading.Event()
        pending_approval["event"] = approval_event

        # Hide "Always" button for high-risk tools
        approve_always_btn.layout.display = 'none' if tool_name in HIGH_RISK_TOOLS else 'inline-block'

        dark = ui_state.get("dark_mode", True)
        card_bg = "#2b2b1f" if dark else "#fff8e1"
        card_fg = "#f0f0f0" if dark else "#111"
        card_border = "#555" if dark else "#e6d9aa"
        pre_bg = "#1f1f1f" if dark else "#fff"
        pre_border = "#444" if dark else "#ddd"

        approval_box.layout.border = f"1px solid {card_border}"
        approval_box.layout.padding = "6px"
        approval_box.layout.border_radius = "6px"
        approval_box.layout.background = "#1e1e1e" if dark else "#fafafa"

        with approval_output:
            clear_output()
            # Show FULL payload (up to 4000 chars) so user can review all code
            raw_input = json.dumps(tool_input, indent=2, default=str)
            truncated = len(raw_input) > 4000
            input_str = escape_html(raw_input[:4000])
            if truncated:
                input_str += f"\n\n... [{len(raw_input):,} chars total — showing first 4000]"
            safe_tool_name = escape_html(tool_name)
            risk_label = ' <span style="color:#f44336">[HIGH RISK - review carefully]</span>' if tool_name in HIGH_RISK_TOOLS else ''
            display(HTML(
                f'<div style="padding:10px;background:{card_bg};border:1px solid {card_border};border-radius:5px;color:{card_fg};">'
                f'<h4 style="margin:0 0 8px 0;color:{card_fg};">Approval Required{risk_label}</h4>'
                f'<p style="margin:0 0 8px 0;color:{card_fg};"><b>Tool:</b> {safe_tool_name}</p>'
                f'<pre style="font-size:11px;color:{card_fg};background:{pre_bg};border:1px solid {pre_border};margin:0;padding:8px;border-radius:4px;max-height:400px;overflow:auto;white-space:pre-wrap;">{input_str}</pre>'
                f'</div>'
            ))
        approval_box.layout.display = 'block'
        # Keep Send button DISABLED during approval — require explicit Approve/Deny click
        # (prevents accidental approval from pressing Send/Enter out of habit)
        send_btn.disabled = True
        send_btn.layout.display = 'none'
        input_box.placeholder = 'Use Approve or Deny buttons above...'

        # Wait with timeout (5 min max)
        max_wait = 300
        waited = 0
        while pending_approval["result"] is None and waited < max_wait:
            if ui_state.get("stop_requested"):
                pending_approval["result"] = False
                break
            approval_event.wait(timeout=0.1)
            waited += 0.1

        approval_box.layout.display = 'none'
        # Restore Send button to hidden state (agent still running)
        send_btn.disabled = True
        send_btn.layout.display = 'none'
        input_box.placeholder = 'Type your message...'
        pending_approval["event"] = None  # Clear stale event reference

        with approval_output:
            clear_output()

        result = pending_approval["result"]
        if result is None:
            result = False  # Timeout = deny
            add_message('system', f'[TIMEOUT] Auto-denied: {tool_name}')
        else:
            add_message('system', f'{"[OK] Approved" if result else "[X] Denied"}: {tool_name}')
        return result

    def on_approve(b):
        pending_approval["result"] = True
        if pending_approval.get("event"):
            pending_approval["event"].set()

    def on_approve_always(b):
        pending_approval["result"] = True
        # Add tool to always-allow list for this session
        if "always_allow" not in ui_state:
            ui_state["always_allow"] = set()
        if pending_approval.get("tool_name"):
            ui_state["always_allow"].add(pending_approval["tool_name"])
        if pending_approval.get("event"):
            pending_approval["event"].set()

    def on_deny(b):
        pending_approval["result"] = False
        if pending_approval.get("event"):
            pending_approval["event"].set()

    approve_btn.on_click(on_approve)
    approve_always_btn.on_click(on_approve_always)
    deny_btn.on_click(on_deny)

    # --- ask_user handlers ---
    def on_ask_user_submit(b):
        pending_user_input["result"] = ask_user_input.value.strip() or "(no response)"
        if pending_user_input.get("event"):
            pending_user_input["event"].set()

    def on_ask_user_skip(b):
        pending_user_input["result"] = "(user skipped)"
        if pending_user_input.get("event"):
            pending_user_input["event"].set()

    ask_user_submit.on_click(on_ask_user_submit)
    ask_user_skip.on_click(on_ask_user_skip)

    def request_user_input(question: str, options: list = None) -> str:
        """Show a text input dialog and wait for the user's response."""
        pending_user_input["result"] = None
        user_input_event = threading.Event()
        pending_user_input["event"] = user_input_event
        ask_user_input.value = ""

        dark = ui_state.get("dark_mode", True)
        card_bg = "#2b2b3f" if dark else "#f0f4ff"
        card_fg = "#f0f0f0" if dark else "#111"
        card_border = "#5577aa" if dark else "#aac4e6"

        with ask_user_output:
            clear_output()
            q_html = escape_html(question)
            opts_html = ""
            if options and isinstance(options, list):
                opts_html = "<ul>" + "".join(f"<li>{escape_html(str(o))}</li>" for o in options) + "</ul>"
            display(HTML(
                f'<div style="padding:10px;background:{card_bg};border:1px solid {card_border};border-radius:5px;color:{card_fg};">'
                f'<h4 style="margin:0 0 8px 0;color:{card_fg};">Agent Question</h4>'
                f'<p style="margin:0 0 8px 0;color:{card_fg};">{q_html}</p>'
                f'{opts_html}</div>'
            ))
        ask_user_box.layout.display = 'block'
        # Enable Send button as fallback — user can type answer in chat input and press Send
        # (fixes SageMaker Studio where dedicated Submit/Skip buttons may not fire)
        send_btn.disabled = False
        send_btn.layout.display = 'inline-block'
        input_box.placeholder = 'Type your answer here and press Send (or use Submit above)...'

        # Wait with timeout (5 min max)
        max_wait = 300
        waited = 0
        while pending_user_input["result"] is None and waited < max_wait:
            if ui_state.get("stop_requested"):
                pending_user_input["result"] = "(stopped)"
                break
            user_input_event.wait(timeout=0.1)
            waited += 0.1

        ask_user_box.layout.display = 'none'
        # Restore Send button to hidden state (agent still running)
        send_btn.disabled = True
        send_btn.layout.display = 'none'
        input_box.placeholder = 'Type your message...'
        pending_user_input["event"] = None  # Clear stale event reference
        with ask_user_output:
            clear_output()

        result = pending_user_input["result"]
        if result is None:
            result = "(timed out — no response)"
        add_message('system', f'User answered: {result}')
        return result

    def on_stop(b):
        """Handle stop button click - also kills active subprocesses."""
        ui_state["stop_requested"] = True
        _kill_active_process()  # Kill any running bash/python_exec subprocess
        if pending_approval.get("event"):
            pending_approval["result"] = False
            pending_approval["event"].set()
        if pending_user_input.get("event"):
            pending_user_input["result"] = "(stopped)"
            pending_user_input["event"].set()
        approval_box.layout.display = 'none'
        ask_user_box.layout.display = 'none'
        with approval_output:
            clear_output()
        with ask_user_output:
            clear_output()
        send_btn.disabled = False
        status_html.value = '<span style="color:#ff9800"><b>[STOP] Stop requested...</b></span>'
        add_message('system', '[STOP] Stop requested - killing active processes')

    stop_btn.on_click(on_stop)

    def do_pre_send_compact():
        """Compact before sending if context >= 80% (prevents mid-response overflow)."""
        global _auto_compact_paused
        if not ui_state["agent"] or not ui_state["agent"].messages:
            return False

        usage = CONTEXT.get_usage(ui_state["agent"].messages)
        pct = usage["percent"] * 100

        if pct >= 80 and auto_compact_checkbox.value and not _auto_compact_paused:  # V4: circuit breaker
            add_message('system', f'[...] Pre-send compact (context at {pct:.0f}%)...')
            try:
                messages = ui_state["agent"].messages
                # Stage 1: Prune old tool outputs first (cheap, no LLM call)
                pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, CONFIG.context_max_tokens)
                if tokens_saved > 0:
                    ui_state["agent"].messages = pruned_msgs
                    messages = pruned_msgs
                    FILE_CACHE.clear_context()
                    # Re-check — prune alone may be sufficient
                    usage = CONTEXT.get_usage(messages)
                    new_pct = usage["percent"] * 100
                    if new_pct < 75:
                        add_message('system', f'[OK] Pruned only. Context: {pct:.0f}% -> {new_pct:.0f}%')
                        if "always_allow" in ui_state:  # V4.2 V2-D: expire approvals on prune-only too
                            ui_state["always_allow"].clear()
                        return True
                # Stage 2: LLM summary only if still above threshold
                summary = COMPACTOR.create_llm_summary(ui_state["client"], messages)
                # V4 circuit breaker: track failures from UI pre-send path too
                if summary is None:
                    agent = ui_state["agent"]
                    agent._compact_failure_count += 1
                    if agent._compact_failure_count >= MAX_COMPACT_FAILURES:
                        _auto_compact_paused = True
                        add_message('system', f'[!] Compact failed {MAX_COMPACT_FAILURES} times. Auto-compact paused.')
                    summary = "Conversation compacted (summary unavailable). Continue from recent context."
                else:
                    ui_state["agent"]._compact_failure_count = 0
                compacted = COMPACTOR.compact(messages, summary)
                ui_state["agent"].messages = compacted
                FILE_CACHE.clear_context()
                ui_state.get("always_allow", set()).clear()  # V4.2 V2-D: expire stale approvals
                usage = CONTEXT.get_usage(compacted)
                new_pct = usage["percent"] * 100
                add_message('system', f'[OK] Pre-compacted. Context: {pct:.0f}% -> {new_pct:.0f}%')
                return True
            except Exception as e:
                add_message('system', f'Pre-compact failed: {e}')
        elif _auto_compact_paused and pct >= 80:
            add_message('system', '[!] Auto-compact paused (too many failures). Use manual Compact button.')
        return False

    def on_send(b):
        # Lock is set by _on_send_threaded wrapper before spawning this thread.
        # All paths must release lock — use _release_lock() helper for early returns.
        def _release_lock():
            ui_state["lock"] = False
            send_btn.disabled = False
            send_btn.layout.display = 'inline-block'
            stop_btn.layout.display = 'none'

        msg = input_box.value.strip()
        if not msg:
            _release_lock()
            return

        # Optional auth gate for multi-user/shared notebook setups.
        if CONFIG.require_auth and not ui_state.get("authenticated", False):
            auth_token = os.getenv(CONFIG.auth_token_env, "")
            if msg.startswith("/auth "):
                provided = msg[len("/auth "):].strip()
                input_box.value = ""
                if auth_token and provided == auth_token:
                    ui_state["authenticated"] = True
                    add_message('system', 'Authentication successful.')
                else:
                    add_message('system', 'Authentication failed. Use /auth <token>.')
                _release_lock()
                return
            add_message('system', f'Authentication required. Send /auth <token> (env: {CONFIG.auth_token_env}).')
            input_box.value = ""
            _release_lock()
            return

        # Local skill commands (v4)
        if msg == "/skills":
            skills = SKILLS.list_skills()
            if not skills:
                add_message('system', f'No skills found in {SKILLS.skills_dir}')
            else:
                add_message('system', "Available skills:\n" + "\n".join([f"- **{s['name']}**: {s['description']}" for s in skills]))
            input_box.value = ""
            _release_lock()
            return
        if msg.startswith("/skill use "):
            name = msg[len("/skill use "):].strip()
            ok, _content = SKILLS.read_skill(name)
            if not ok:
                add_message('system', f'Skill not found: {name}')
            else:
                active = ui_state.get("active_skills", [])
                if name not in active:
                    active.append(name)
                    ui_state["active_skills"] = active
                # V4.9.1: explicit /skill use lifts any prior /unskill or /skill clear deactivation.
                _deact = ui_state.get("deactivated_skills", set())
                if name in _deact:
                    _deact.discard(name)
                    ui_state["deactivated_skills"] = _deact
                with SKILLS._pending_lock:
                    SKILLS.active_skill = name
                add_message('system', f'Enabled skill: {name}')
                update_mode_display()
            input_box.value = ""
            _release_lock()
            return
        if msg == "/skill clear":
            # V4.9.1: remember which skills were cleared so auto-match can't silently re-match them.
            prev_active = list(ui_state.get("active_skills", []))
            ui_state["active_skills"] = []
            ui_state["deactivated_skills"] = ui_state.get("deactivated_skills", set()) | set(prev_active)
            with SKILLS._pending_lock:
                SKILLS.active_skill = None
                SKILLS._pending_activations.clear()
            sticky_note = f' (sticky: {", ".join(sorted(ui_state["deactivated_skills"]))})' if ui_state["deactivated_skills"] else ""
            add_message('system', f'Cleared active skills{sticky_note}')
            update_mode_display()
            input_box.value = ""
            _release_lock()
            return
        # V4.9.1: /unskill <name> — deactivate one specific skill (stays off for the session)
        if msg.startswith("/unskill "):
            name = msg[len("/unskill "):].strip()
            if not name:
                add_message('system', 'Usage: /unskill <skill-name>  — see /skills for the list')
            elif name not in SKILLS._cache:
                _available = ", ".join(sorted(SKILLS._cache.keys())) if SKILLS._cache else "none"
                add_message('system', f'Skill not found: {name}. Available: {_available}')
            else:
                active = ui_state.get("active_skills", [])
                was_active = name in active
                ui_state["active_skills"] = [s for s in active if s != name]
                ui_state["deactivated_skills"] = ui_state.get("deactivated_skills", set()) | {name}
                with SKILLS._pending_lock:
                    if SKILLS.active_skill == name:
                        SKILLS.active_skill = None
                verb = "Deactivated" if was_active else "Blocked auto-match for"
                add_message('system', f'{verb} skill: {name}  (stays off until /skill use {name} or new session)')
                update_mode_display()
            input_box.value = ""
            _release_lock()
            return
        # V4.9.1: /skill use <name> lifts any prior deactivation so the user can explicitly re-enable.
        # V4.9.5: skill self-patching commands — review/apply/reject pending proposals
        if msg == "/skill suggestions" or msg == "/skill suggestion":
            proposals = SKILLS.list_proposals()
            if not proposals:
                add_message('system', 'No pending skill patches.\n\n'
                                      f'Skill patching is currently {"ON" if CONFIG.enable_skill_patching else "OFF"} '
                                      f'(toggle via CONFIG.enable_skill_patching).')
            else:
                lines = [f'Pending skill patches ({len(proposals)}):']
                for p in proposals:
                    lines.append(f'  - {p["skill"]:<20} proposed {p["ts"]}')
                    if p.get("reason"):
                        lines.append(f'    reason: {p["reason"]}')
                lines.append('')
                lines.append('Review with: /skill apply <name>   (or /skill reject <name>)')
                add_message('system', '\n'.join(lines))
            input_box.value = ""
            _release_lock()
            return
        if msg.startswith("/skill apply "):
            raw = msg[len("/skill apply "):].strip()
            # Parse optional --yes / --edit flag
            force = False
            edit_first = False
            parts = raw.split()
            name = parts[0] if parts else ""
            for p in parts[1:]:
                if p == "--yes":
                    force = True
                elif p == "--edit":
                    edit_first = True
            if not name:
                add_message('system', 'Usage: /skill apply <name> [--yes|--edit]\n  See /skill suggestions for pending patches.')
            else:
                proposal = SKILLS.get_latest_proposal(name)
                if not proposal:
                    add_message('system', f'No pending proposals for skill "{name}". Use /skill suggestions to list all.')
                elif edit_first:
                    add_message('system', f'Edit the proposal at: {proposal["path"]}\nThen run: /skill apply {name} --yes')
                elif not force:
                    # Show diff preview
                    skill = SKILLS._cache.get(name)
                    live_text = ""
                    proposed_text = ""
                    try:
                        live_text = open(skill.location, encoding="utf-8").read()
                        proposed_text = open(proposal["path"], encoding="utf-8").read()
                        # Strip metadata header from proposed for accurate diff
                        if proposed_text.lstrip().startswith("<!--"):
                            end = proposed_text.find("-->")
                            if end != -1:
                                proposed_text = proposed_text[end + 3:].lstrip()
                    except Exception as e:
                        add_message('system', f'Failed to read files for diff: {e}')
                        input_box.value = ""
                        _release_lock()
                        return
                    import difflib as _difflib
                    diff = list(_difflib.unified_diff(
                        live_text.splitlines(keepends=True),
                        proposed_text.splitlines(keepends=True),
                        fromfile=f'live/{name}/SKILL.md',
                        tofile=f'proposed/{name}/SKILL.md',
                        n=3,
                    ))
                    diff_text = "".join(diff) if diff else "(no differences detected)"
                    add_message('system',
                        f"Diff for skill '{name}' (proposed {proposal['ts']}):\n\n"
                        f"```diff\n{diff_text}\n```\n\n"
                        f"Reason given: \"{proposal.get('reason', '(none)')}\"\n\n"
                        f"Apply? Type:\n"
                        f"  /skill apply {name} --yes        (apply now)\n"
                        f"  /skill apply {name} --edit       (open the .proposed file and tweak first)\n"
                        f"  /skill reject {name}             (discard, never apply)"
                    )
                else:
                    ok, message = SKILLS.apply_proposal(name)
                    add_message('system', f'{"OK" if ok else "FAIL"}: {message}')
                    update_mode_display()
            input_box.value = ""
            _release_lock()
            return
        if msg.startswith("/skill reject "):
            name = msg[len("/skill reject "):].strip()
            if not name:
                add_message('system', 'Usage: /skill reject <name>')
            else:
                ok, message = SKILLS.reject_proposal(name)
                add_message('system', f'{"OK" if ok else "FAIL"}: {message}')
            input_box.value = ""
            _release_lock()
            return
        if msg == "/revert" or msg.startswith("/revert "):
            raw = msg[len("/revert"):].strip()
            # Support "--yes" flag for confirmed revert (skip preview)
            force = False
            if raw.endswith(" --yes") or raw == "--yes":
                force = True
                raw = raw[:-len("--yes")].strip()
            target = raw
            if target == "all":
                if not force:
                    snaps = SNAPSHOTS.list_snapshots()
                    files = sorted(set(e["rel"] for e in snaps))
                    result = (
                        f"⚠ /revert all would restore {len(files)} file(s) to earliest snapshot:\n"
                        + "\n".join(f"- {f}" for f in files)
                        + "\n\nThis is destructive. Confirm with `/revert all --yes`."
                    )
                else:
                    result = SNAPSHOTS.revert_all()
            elif target:
                abs_path = os.path.join(CONFIG.workspace, target) if not os.path.isabs(target) else target
                matching = [e for e in SNAPSHOTS.list_snapshots() if e["file"] == abs_path]
                if not matching:
                    result = f"No snapshots for {target}"
                elif not force:
                    # Show diff preview between current file and snapshot
                    latest = matching[-1]
                    snap_time = time.strftime('%H:%M:%S', time.localtime(latest['time']))
                    try:
                        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                            current = f.read()
                    except Exception:
                        current = ""
                    try:
                        with open(latest['snapshot'], 'r', encoding='utf-8', errors='replace') as f:
                            snapshot = f.read()
                    except Exception:
                        snapshot = ""
                    if current == snapshot:
                        result = f"✓ {target} already matches snapshot from {snap_time}. Nothing to revert."
                    else:
                        # Diff is FROM current TO snapshot (showing what revert will undo)
                        diff_text = _generate_unified_diff(abs_path, current, snapshot)
                        # Truncate very long diffs
                        if len(diff_text) > 6000:
                            diff_text = diff_text[:6000] + "\n... (diff truncated)"
                        result = (
                            f"**Preview:** `/revert {target}` will restore snapshot from {snap_time}.\n"
                            f"Diff (current → snapshot):\n```diff\n{diff_text}\n```\n"
                            f"Confirm with `/revert {target} --yes`"
                        )
                else:
                    ok, result = SNAPSHOTS.revert(abs_path)
            else:
                snaps = SNAPSHOTS.list_snapshots()
                if not snaps:
                    result = "No snapshots available. Files are snapshotted before each edit."
                else:
                    files = set(e["rel"] for e in snaps)
                    result = f"Files with snapshots ({len(files)}):\n" + "\n".join(f"- {f}" for f in sorted(files))
                    result += "\n\nUse `/revert <file>` (shows preview) then `/revert <file> --yes` to confirm, or `/revert all --yes`."
            add_message('system', result)
            input_box.value = ""
            _release_lock()
            return
        if msg == "/cost":
            stats = TOKENS.get_stats()
            pricing = _MODEL_PRICING.get(CONFIG.model_id)
            rate_str = ""
            if pricing:
                rate_str = f"\n- Rate: ${pricing['input']*1000:.2f} / ${pricing['output']*1000:.2f} per 1M in/out"
            overhead = TOKENS.get_fixed_overhead()
            last_cost = stats['last_cost_usd']
            last_fmt = f"${last_cost:.4f}" if last_cost < 0.01 else f"${last_cost:.2f}"
            add_message('system',
                f"Session Cost: **{TOKENS.get_cost()}**\n"
                f"- Input: {stats['session_input']:,} tokens\n"
                f"- Output: {stats['session_output']:,} tokens\n"
                f"- Cache read: {stats['session_cache_read']:,} tokens\n"
                f"- API calls: {stats['api_calls']}\n"
                f"- Last call cost: {last_fmt}\n"
                f"- Model: {CONFIG.model_id}{rate_str}\n"
                f"- Fixed overhead/call: ~{overhead:,} tokens (system prompt + tool schemas + Bedrock)")
            input_box.value = ""
            _release_lock()
            return
        # /context command - inspect context/token bloat sources
        if msg == "/context":
            agent = ui_state.get("agent")
            if not agent:
                add_message('system', 'No active agent session yet.')
            else:
                add_message('system', format_context_report(agent.messages))
            input_box.value = ""
            _release_lock()
            return
        # /status command - inspect or initialize durable long-running task state
        if msg == "/status" or msg.startswith("/status "):
            arg = msg[len("/status"):].strip()
            status_path = _status_doc_path()
            if not status_path:
                add_message('system', 'Status doc is disabled or outside workspace. Check `CONFIG.status_doc`.')
            elif arg == "path":
                add_message('system', f'Status doc path: `{status_path}`')
            elif arg == "init":
                try:
                    if os.path.exists(status_path):
                        add_message('system', f'AGENT_STATUS.md already exists: `{status_path}`')
                    else:
                        os.makedirs(os.path.dirname(status_path), exist_ok=True)
                        with open(status_path, "w", encoding="utf-8") as f:
                            f.write(_status_doc_template())
                        add_message('system', f'Initialized AGENT_STATUS.md: `{status_path}`')
                except Exception as e:
                    add_message('system', f'Failed to initialize AGENT_STATUS.md: {e}')
            else:
                if not os.path.isfile(status_path):
                    add_message('system', f'No AGENT_STATUS.md found at `{status_path}`. Use `/status init` to create the template.')
                else:
                    loaded = _load_project_status().strip()
                    if loaded:
                        if len(loaded) > 8000:
                            loaded = loaded[:8000] + "\n... (truncated for display)"
                        add_message('system', loaded)
                    else:
                        add_message('system', f'AGENT_STATUS.md exists but is empty or disabled: `{status_path}`')
            input_box.value = ""
            _release_lock()
            return
        # /verify command - auto-loads verify skill and runs verification
        if msg == "/verify" or msg.startswith("/verify "):
            scope = msg[len("/verify"):].strip() or "full"
            ok, _content = SKILLS.read_skill("verify")
            if ok:
                active = ui_state.get("active_skills", [])
                if "verify" not in active:
                    active.append("verify")
                    ui_state["active_skills"] = active
                with SKILLS._pending_lock:
                    SKILLS.active_skill = "verify"
                update_mode_display()
                msg = f"Run {scope} verification on the current project. Follow the verify skill instructions exactly. Run each phase using bash and produce the VERIFICATION REPORT at the end."
                # Fall through to normal send flow
            else:
                add_message('system', 'Verify skill not found. Create skills/verify/SKILL.md')
                input_box.value = ""
                _release_lock()
                return
        # /checkpoint command - save/list/restore named checkpoints
        if msg == "/checkpoint" or msg.startswith("/checkpoint "):
            parts = msg.split(None, 2)
            action = parts[1] if len(parts) > 1 else "create"
            cp_name = parts[2] if len(parts) > 2 else datetime.now().strftime("%H%M")
            if action == "list":
                cps = ui_state.get("checkpoints", [])
                if cps:
                    lines = [f"- **{c['name']}** ({c['time'][:16]}) — {len(c.get('todos', []))} todos, {c.get('exec_calls', 0)} tool calls" for c in cps]
                    add_message('system', f"Checkpoints ({len(cps)}):\n" + "\n".join(lines))
                else:
                    add_message('system', 'No checkpoints saved. Use `/checkpoint create <name>`')
            elif action == "restore":
                # /checkpoint restore <name> — restore todos from a named checkpoint
                target_name = parts[2].strip() if len(parts) > 2 else ""
                cps = ui_state.get("checkpoints", [])
                if not target_name:
                    add_message('system', 'Usage: `/checkpoint restore <name>` — see `/checkpoint list`')
                else:
                    match = next((c for c in reversed(cps) if c.get("name") == target_name), None)
                    if not match:
                        add_message('system', f'No checkpoint named "{target_name}". Use `/checkpoint list`.')
                    else:
                        try:
                            global _TODOS
                            _TODOS = copy.deepcopy(match.get("todos", []))
                            ui_state["todos"] = list(_TODOS)
                        except Exception as _e:
                            add_message('system', f'Restore partial failure: {_e}')
                        files_mod = match.get("files_modified", [])
                        files_list = "\n".join(f"- {f}" for f in files_mod) if files_mod else "(none)"
                        add_message('system',
                            f'✓ Restored todos from checkpoint **{target_name}** ({match.get("time","")[:16]}).\n'
                            f'- Todos restored: {len(match.get("todos", []))}\n'
                            f'- Files that had been modified at checkpoint time:\n{files_list}\n\n'
                            f'Files are NOT auto-reverted. Review and use `/revert <file>` per file if needed.'
                        )
                        try:
                            render_chat()
                        except Exception:
                            pass
            else:  # "create" or any other word treated as checkpoint name
                if action not in ("list", "create"):
                    cp_name = action  # /checkpoint my-milestone → name = "my-milestone"
                # Sanitize checkpoint name
                cp_name = re.sub(r'[^\w\s\-.]', '', cp_name)[:50].strip() or datetime.now().strftime("%H%M")
                snapshot_files = []
                try:
                    snaps = SNAPSHOTS.list_snapshots()
                    snapshot_files = list(set(e.get("rel", "") for e in snaps)) if snaps else []
                except Exception:
                    pass
                checkpoint = {
                    "name": cp_name,
                    "time": datetime.now().isoformat(),
                    "todos": copy.deepcopy(_TODOS) if _TODOS else [],
                    "files_modified": snapshot_files,
                    "exec_calls": ui_state["agent"].exec_calls if ui_state.get("agent") else 0,
                    "token_stats": TOKENS.get_stats(),
                }
                cps = ui_state.setdefault("checkpoints", [])
                cps.append(checkpoint)
                if len(cps) > 50:
                    ui_state["checkpoints"] = cps[-50:]
                add_message('system', f'Checkpoint saved: {cp_name} ({len(snapshot_files)} files modified, {len(_TODOS) if _TODOS else 0} todos)')
            input_box.value = ""
            _release_lock()
            return

        # /phase command - set current work phase shown in status bar
        if msg == "/phase" or msg.startswith("/phase "):
            new_phase = msg[len("/phase"):].strip()
            if not new_phase:
                current = ui_state.get("session_phase", "")
                add_message('system', f'Current phase: **{current or "(none)"}**\nUsage: `/phase <text>` or `/phase clear`')
            elif new_phase.lower() == "clear":
                ui_state["session_phase"] = ""
                add_message('system', 'Phase cleared.')
            else:
                ui_state["session_phase"] = new_phase[:80]
                add_message('system', f'Phase set: **{new_phase[:80]}**')
            update_mode_display()
            update_tokens_display()
            input_box.value = ""
            _release_lock()
            return
        # /diffs command - show recent edit diffs this session
        if msg == "/diffs" or msg.startswith("/diffs "):
            arg = msg[len("/diffs"):].strip()
            with _RECENT_DIFFS_LOCK:
                diffs = list(_RECENT_DIFFS)
            if not diffs:
                add_message('system', 'No edits yet this session. Diffs are recorded on every Write/Edit.')
            elif arg == "summary" or not arg:
                # Per-file summary: file -> count
                counts = {}
                for d in diffs:
                    f = d.get("file", "?")
                    counts[f] = counts.get(f, 0) + 1
                lines = [f"- `{os.path.relpath(f, CONFIG.workspace) if f.startswith(CONFIG.workspace) else f}` — {n} edit(s)" for f, n in sorted(counts.items())]
                add_message('system',
                    f'**Session edits:** {len(diffs)} total across {len(counts)} file(s)\n'
                    + "\n".join(lines)
                    + "\n\nUse `/diffs <file>` to see full diff, `/diffs last` for the most recent."
                )
            elif arg == "last":
                d = diffs[-1]
                diff_text = d.get("diff", "(empty)")
                if len(diff_text) > 6000:
                    diff_text = diff_text[:6000] + "\n... (truncated)"
                rel = os.path.relpath(d["file"], CONFIG.workspace) if d["file"].startswith(CONFIG.workspace) else d["file"]
                add_message('system', f'**Last edit:** `{rel}`\n```diff\n{diff_text}\n```')
            else:
                # Filter by filename substring
                matches = [d for d in diffs if arg in d.get("file", "")]
                if not matches:
                    add_message('system', f'No diffs matching "{arg}". Try `/diffs summary`.')
                else:
                    chunks = []
                    for d in matches[-3:]:  # last 3 matching
                        diff_text = d.get("diff", "")
                        if len(diff_text) > 3000:
                            diff_text = diff_text[:3000] + "\n... (truncated)"
                        rel = os.path.relpath(d["file"], CONFIG.workspace) if d["file"].startswith(CONFIG.workspace) else d["file"]
                        chunks.append(f'**{rel}**\n```diff\n{diff_text}\n```')
                    add_message('system', f'Showing last {len(chunks)} of {len(matches)} diffs matching "{arg}":\n\n' + "\n\n".join(chunks))
            input_box.value = ""
            _release_lock()
            return
        # /regression command - thin wrapper: git diff HEAD + session diff summary + suggested test cmd
        if msg == "/regression" or msg.startswith("/regression "):
            try:
                gd = subprocess.run(
                    ["git", "diff", "HEAD", "--stat"],
                    capture_output=True, text=True, timeout=5, cwd=CONFIG.workspace
                )
                git_stat = gd.stdout.strip() if gd.returncode == 0 else f"(not a git repo or no HEAD: {gd.stderr.strip()[:200]})"
            except Exception as e:
                git_stat = f"(git unavailable: {e})"
            with _RECENT_DIFFS_LOCK:
                diffs = list(_RECENT_DIFFS)
            if diffs:
                counts = {}
                for d in diffs:
                    f = d.get("file", "?")
                    counts[f] = counts.get(f, 0) + 1
                sess_lines = [f"- `{os.path.relpath(f, CONFIG.workspace) if f.startswith(CONFIG.workspace) else f}` — {n} edit(s)" for f, n in sorted(counts.items())]
                session_block = f"**Session edits:** {len(diffs)} total across {len(counts)} file(s)\n" + "\n".join(sess_lines)
            else:
                session_block = "**Session edits:** none yet"
            has_pytest = any(os.path.isfile(os.path.join(CONFIG.workspace, m)) for m in ("pytest.ini", "pyproject.toml", "conftest.py"))
            test_suggest = "pytest -x -q" if has_pytest else "python -m unittest discover -v"
            add_message('system',
                f"**Regression check:**\n\n"
                f"**git diff HEAD --stat:**\n```\n{git_stat or '(no uncommitted changes)'}\n```\n\n"
                f"{session_block}\n\n"
                f"**Suggested test command:** `bash {test_suggest}`\n"
                f"Run it via bash to verify nothing broke. Or run `/verify` for adversarial testing + skill-driven report."
            )
            input_box.value = ""
            _release_lock()
            return
        # /done command - chain simplify → verify → gate verdict before declaring complete
        if msg == "/done" or msg.startswith("/done "):
            scope = msg[len("/done"):].strip() or "full"
            simplify_ok, _ = SKILLS.read_skill("simplify")
            verify_ok, _ = SKILLS.read_skill("verify")
            if not (simplify_ok and verify_ok):
                missing = []
                if not simplify_ok: missing.append("skills/simplify/SKILL.md")
                if not verify_ok: missing.append("skills/verify/SKILL.md")
                add_message('system', f'/done requires skills: missing {", ".join(missing)}')
                input_box.value = ""
                _release_lock()
                return
            active = ui_state.get("active_skills", [])
            for s in ("simplify", "verify"):
                if s not in active:
                    active.append(s)
            ui_state["active_skills"] = active
            with SKILLS._pending_lock:
                SKILLS.active_skill = "verify"
            ui_state["session_phase"] = f"done-gate:{scope}"
            update_mode_display()
            update_tokens_display()
            msg = (
                f"Run the DONE gate ({scope}) on the current project. Two phases, do NOT skip:\n\n"
                f"**Phase 1 — SIMPLIFY:** Follow skills/simplify/SKILL.md. Review all files edited this session "
                f"(use `/diffs summary` mental model) for reuse opportunities, dead code, unnecessary complexity, and over-engineering. "
                f"Auto-fix what you find. Report what was changed or confirm 'nothing to simplify'.\n\n"
                f"**Phase 2 — VERIFY:** Follow skills/verify/SKILL.md exactly. Run BUILD, BASELINE tests, TYPE-SPECIFIC tests, "
                f"and ADVERSARIAL PROBES. Try to BREAK the implementation, not confirm it works.\n\n"
                f"**Final verdict:** Produce a DONE REPORT at the end with:\n"
                f"- SIMPLIFY: <what was changed, or 'nothing'>\n"
                f"- VERIFY: PASS / FAIL / PARTIAL with evidence (command + output)\n"
                f"- FINAL: READY-TO-SHIP / NEEDS-WORK / BLOCKED\n\n"
                f"If FINAL is not READY-TO-SHIP, list specific next actions. Do NOT claim done unless VERIFY = PASS."
            )
            # Fall through to normal send flow

        # Custom commands from agent_config.json
        if msg.startswith("/") and not msg.startswith("/auth"):
            cmd_parts = msg[1:].split(None, 1)
            cmd_name = cmd_parts[0] if cmd_parts else ""
            cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""

            if cmd_name == "commands":
                cmds = COMMANDS.list_commands()
                if cmds:
                    lines = [f"- **/{c['name']}**: {c['description']}" for c in cmds]
                    add_message('system', "Available commands:\n" + "\n".join(lines))
                else:
                    add_message('system', "No custom commands configured. Add commands in agent_config.json.")
                input_box.value = ""
                _release_lock()
                return

            expanded = COMMANDS.expand(cmd_name, cmd_args)
            if expanded is not None:
                cmd_agent = COMMANDS.get_agent(cmd_name)
                if cmd_agent:
                    add_message('system', f'Expanding /{cmd_name} (agent: {cmd_agent})...')
                else:
                    add_message('system', f'Expanding /{cmd_name}...')
                msg = expanded  # Replace msg with expanded template
                # Store agent type and command name for the send flow
                ui_state["_cmd_agent_type"] = cmd_agent
                ui_state["_cmd_name"] = cmd_name
                # Fall through to normal send flow

        ui_state["lock"] = True
        ui_state["stop_requested"] = False  # Reset stop flag
        send_btn.disabled = True
        send_btn.layout.display = 'none'  # Hide send
        stop_btn.layout.display = 'inline-block'  # Show stop
        input_box.value = ''

        add_message('user', msg)
        status_html.value = '<span style="color:#ff9800"><b>⋯ Processing...</b></span>'

        # Create agent if needed
        if ui_state["agent"] is None:
            TOKENS.reset()
            # Use provided session name, or auto-generate from first message
            session_title = session_name_input.value.strip() if session_name_input.value.strip() else f"Chat: {msg[:40]}"
            session = SESSIONS.create(title=session_title)
            ui_state["session"] = session
            ui_state["agent"] = Agent(
                ui_state["client"],
                session.id,
                on_approval=request_approval,
                on_ask_user=request_user_input,
                on_tokens=lambda stats: update_tokens_display(),
                on_thinking=lambda t: add_message('thinking', t) if t else None,
                on_stop_check=lambda: ui_state.get("stop_requested", False),
                on_compact_fn=lambda: ui_state["always_allow"].clear() if "always_allow" in ui_state else None,  # V4.2 V2-D
            )
            session_name_input.value = ''  # Clear for next session

        # Track displayed tool results to prevent duplicates
        displayed_tools = set()

        def output_fn(text):
            """Handle agent output."""
            # Skip "Calling..." messages - only show results
            if text.startswith('[Calling '):
                return  # Don't display, wait for result

            # Check for tool result pattern: [tool_name result]:
            tool_result_match = re.match(r'^\[(\w+)\s+result\]:', text)
            if tool_result_match:
                tool = tool_result_match.group(1)
                result = text[tool_result_match.end():].strip()

                # Dedup: create key from tool name + first 100 chars of result
                dedup_key = f"{tool}:{result[:100]}"
                if dedup_key in displayed_tools:
                    return  # Skip duplicate
                displayed_tools.add(dedup_key)

                add_message('tool', result, tool)
                update_tokens_display()
                return

            if text.startswith('[Warning') or text.startswith('[!') or text.startswith('[i]'):
                add_message('system', text)
            elif text.startswith('[Reached'):
                add_message('system', text)
            elif text.strip():
                add_message('assistant', text)
                update_tokens_display()

        try:
            # Pre-send compact check (prevents mid-response overflow)
            do_pre_send_compact()

            # Check if stop was requested during pre-compact
            if ui_state["stop_requested"]:
                add_message('system', '[STOP] Stopped before sending')
                return

            # Determine system prompt based on plan mode
            if plan_mode_toggle.value:
                add_message('system', '[PLAN] PLAN MODE: Agent will explore and create a plan (no modifications)')
                system_prompt = SYSTEM_PROMPT + "\n\n" + PLAN_MODE_PROMPT
            else:
                system_prompt = None  # Use default

            # Auto-match skills by keyword (model-independent — works even with small models)
            # V4.9.6: Entire feature is global opt-in. Default is OFF so skills never
            # silently load into context unless the user intentionally enables it.
            # V4.9.0: Two fixes compared to v4.8.0:
            #   1. Honour auto_trigger: false (v4.8.0 parsed the flag but the loop ignored it).
            #   2. Word-boundary match instead of substring — "clara" no longer matches "Clara_WIP"
            #      via bare `in`, and "review" no longer matches "unreviewable".
            active = ui_state.get("active_skills", [])
            if CONFIG.enable_skill_auto_trigger and msg and not active:
                msg_lower = msg.lower()
                # Extract word tokens once per message (alphanumerics separated by non-word chars).
                msg_words = set(re.findall(r"[a-z0-9]+", msg_lower))
                # V4.9.1: auto-match must also respect user-initiated deactivations (/unskill, /skill clear).
                _deactivated = ui_state.get("deactivated_skills", set())
                for skill_info in SKILLS.list_skills():
                    s_name = skill_info["name"]
                    # V4.9.0: skip skills that opted out of auto-matching.
                    _skill_obj = SKILLS._cache.get(s_name)
                    if _skill_obj is not None and not _skill_obj.auto_trigger:
                        continue
                    # V4.9.1: skip skills the user explicitly deactivated this session.
                    if s_name in _deactivated:
                        continue
                    # Match if every word in the skill name appears as a whole word in the user message.
                    # ("clara-review" -> needs both "clara" AND "review" in the message as complete words.)
                    # V4.9.0 patch: tokenize the skill name with the same regex as the message so names
                    # containing non-hyphen separators (e.g. "qa_review", "docs.v2") are matched consistently.
                    name_words = re.findall(r"[a-z0-9]+", s_name.lower())
                    if name_words and set(name_words).issubset(msg_words):
                        if s_name not in active:
                            active.append(s_name)
                            ui_state["active_skills"] = active
                            with SKILLS._pending_lock:
                                SKILLS.active_skill = s_name
                            # V4.9.0: include approximate injected char count so user sees prompt cost.
                            try:
                                _char_count = os.path.getsize(_skill_obj.location) if _skill_obj else 0
                            except Exception:
                                _char_count = 0
                            _size_hint = f' (~{_char_count} chars injected)' if _char_count else ''
                            add_message('system', f'Auto-matched skill: {s_name}{_size_hint}')
                            break  # Only auto-load one skill

            # Sync skills auto-activated via tool_skill() into ui_state (drains pending list)
            with SKILLS._pending_lock:
                if SKILLS._pending_activations:
                    active = ui_state.get("active_skills", [])
                    for pending_name in SKILLS._pending_activations:
                        if pending_name not in active:
                            active.append(pending_name)
                    ui_state["active_skills"] = active
                    SKILLS._pending_activations.clear()

            # V4: Inject CLAUDE.md project instructions (before active skills so skills can override)
            _base_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
            _project_instructions = load_project_instructions(CONFIG.workspace)
            if _project_instructions:
                _base_prompt = _base_prompt + "\n\n" + _project_instructions
            system_prompt = _base_prompt

            # Append active skills as extra runtime guidance.
            active_skills = ui_state.get("active_skills", [])
            if active_skills:
                blocks = []
                for skill_name in active_skills:
                    ok, txt = SKILLS.read_skill(skill_name, max_chars=8000)
                    if ok and txt.strip():
                        blocks.append(f"[SKILL: {skill_name}]\n{txt}")
                if blocks:
                    system_prompt = system_prompt + "\n\n# Active Skills\n" + "\n\n".join(blocks)

            # If a command specified an agent type, dispatch through sub-agent
            cmd_agent = ui_state.pop("_cmd_agent_type", None)
            cmd_label = ui_state.pop("_cmd_name", "command")
            if cmd_agent and cmd_agent in AGENT_TYPES:
                # Plan Mode safety: force plan agent when Plan Mode is ON
                if plan_mode_toggle.value and cmd_agent != "plan":
                    add_message('system', f'[PLAN] PLAN MODE: /{cmd_label} forced to plan agent (was: {cmd_agent})')
                    cmd_agent = "plan"
                # Route the expanded command through the task sub-agent system
                task_result = ui_state["agent"]._run_task_tool(
                    {"prompt": msg, "subagent_type": cmd_agent, "description": f"/{cmd_label} command"},
                    output_fn
                )
                add_message('assistant', task_result)
            else:
                ui_state["agent"].run(msg, output_fn, system_prompt=system_prompt, plan_mode=plan_mode_toggle.value)

            # Update status when done
            usage = CONTEXT.get_usage(ui_state["agent"].messages)
            pct = usage["percent"] * 100

            # Post-send: prune-only if context still high (no LLM call — pre-send already handles full compact)
            if auto_compact_checkbox.value and pct >= 90 and not ui_state["stop_requested"] and not _auto_compact_paused:  # V4: circuit breaker
                try:
                    pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(ui_state["agent"].messages, CONFIG.context_max_tokens)
                    if tokens_saved > 0:
                        ui_state["agent"].messages = pruned_msgs
                        FILE_CACHE.clear_context()
                        usage = CONTEXT.get_usage(pruned_msgs)
                        pct = usage["percent"] * 100
                        add_message('system', f'[OK] Post-send prune: ~{tokens_saved:,} tokens freed. Context now {pct:.0f}%')
                    if pct >= 90:
                        add_message('system', f'⚠ Context still at {pct:.0f}%. Click Compact for full summarization.')
                except Exception as e:
                    add_message('system', f'Post-send prune failed: {e}')

            # Update status
            if pct >= 90:
                status_html.value = f'<span style="color:#f44336"><b>● Ready ({pct:.0f}% context - HIGH!)</b></span>'
                if not auto_compact_checkbox.value:
                    add_message('system', f'⚠️ Context at {pct:.0f}% - Click "Compact" or enable Auto-Compact.')
            elif pct >= 75:
                status_html.value = f'<span style="color:#ff9800"><b>● Ready ({pct:.0f}% context)</b></span>'
            else:
                status_html.value = f'<span style="color:#4caf50"><b>● Ready ({pct:.0f}% context)</b></span>'

            # Add plan mode indicator to status
            if plan_mode_toggle.value:
                status_html.value = status_html.value.replace('Ready', '[PLAN] Plan Mode')

            update_tokens_display()

        except Exception as e:
            add_message('system', f'Error: {e}')
            import traceback
            traceback.print_exc()

        finally:
            ui_state["lock"] = False
            ui_state["stop_requested"] = False
            send_btn.disabled = False
            send_btn.layout.display = 'inline-block'  # Show send
            stop_btn.layout.display = 'none'  # Hide stop

            # Auto-save session after each message
            if ui_state["agent"] and ui_state["agent"].messages:
                try:
                    # Preserve existing session title; only use input if explicitly set
                    existing_title = ui_state["session"].title if ui_state["session"] else None
                    session_name = session_name_input.value.strip() or existing_title or f"session_{ui_state['agent'].session_id}"
                    ui_state["session"] = Session(
                        id=ui_state["agent"].session_id,
                        created_at=ui_state["session"].created_at if ui_state["session"] else datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat(),
                        title=session_name,
                        messages=copy.deepcopy(ui_state["agent"].messages),
                        metadata={
                            "model": model_dropdown.value,
                            "user_msg_count": ui_state["agent"].user_msg_count,
                            "exec_calls": ui_state["agent"].exec_calls,
                            "exec_seconds": ui_state["agent"].exec_seconds,
                            "active_skills": list(ui_state.get("active_skills", [])),
                            "checkpoints": copy.deepcopy(ui_state.get("checkpoints", [])),
                            "token_stats": TOKENS.get_stats(),
                        },
                        todos=copy.deepcopy(_TODOS) if _TODOS else []
                    )
                    # Async save with fallback — non-blocking but logs failure
                    _session_to_save = ui_state["session"]
                    def _async_save(s):
                        try:
                            SESSIONS.save(s)
                        except Exception as e:
                            logging.warning(f"Async auto-save failed: {e}")
                    threading.Thread(target=_async_save, args=(_session_to_save,), daemon=True).start()
                except Exception as e:
                    add_message('system', f'⚠ Auto-save failed: {e}. Use Save button to retry.')

    def on_clear(b):
        """Clear current session."""
        if ui_state.get("lock"):
            add_message('system', 'Agent is running. Stop it first.')
            return
        global _TODOS, _FILES_READ
        # V4.1 #8: Auto-extract memories at session end if enabled
        if ui_state["agent"]:
            _extract_and_append_memories(ui_state["agent"], output_fn=lambda m: add_message('system', m))
        if ui_state["agent"]:
            ui_state["agent"].reset()
        ui_state["agent"] = None
        ui_state["session"] = None
        _PENDING_IMAGES.clear()  # Clear any queued images
        _TODOS = []
        with _FILES_READ_LOCK:
            _FILES_READ.clear()
            _FILE_READ_TIMES.clear()  # V4: clear staleness tracking on session clear
            _FILE_PARTIAL_READS.clear()  # V4.1 #10: clear partial view tracking
        TOKENS.reset()
        ui_state["messages"] = []
        ui_state["todos"] = []  # Clear todos
        ui_state["active_skills"] = []
        ui_state["deactivated_skills"] = set()  # V4.9.1: sticky deactivations don't carry across sessions
        ui_state["checkpoints"] = []
        with SKILLS._pending_lock:
            SKILLS.active_skill = None
            SKILLS._pending_activations.clear()
        render_chat()
        render_todos()  # Update todo display
        status_html.value = '<span style="color:#4caf50"><b>● Ready</b></span>'
        update_tokens_display()
        update_mode_display()
        update_session_list()

    def on_save(b):
        """Save current session with todos."""
        if ui_state.get("lock"):
            add_message('system', 'Agent is running. Stop it first.')
            return
        if ui_state["session"] and ui_state["agent"]:
            # Update title if user typed a new name
            new_name = session_name_input.value.strip()
            if new_name:
                ui_state["session"].title = new_name
            ui_state["session"].messages = copy.deepcopy(ui_state["agent"].messages)
            metadata = ui_state["session"].metadata or {}
            metadata["model"] = model_dropdown.value
            metadata["user_msg_count"] = ui_state["agent"].user_msg_count
            metadata["exec_calls"] = ui_state["agent"].exec_calls
            metadata["exec_seconds"] = ui_state["agent"].exec_seconds
            metadata["active_skills"] = list(ui_state.get("active_skills", []))
            metadata["checkpoints"] = copy.deepcopy(ui_state.get("checkpoints", []))
            metadata["token_stats"] = TOKENS.get_stats()
            # V4.10.10 in-place: persist session_cost so it survives /save + /load.
            # Previously the running cost would reset to $0.00 on reload — making
            # multi-session cost tracking impossible. Note: `session_cost` lives on
            # the global TOKENS (TokenTracker) singleton, NOT on the Agent — Codex
            # caught this in review. The token_stats dict already returned by
            # TOKENS.get_stats() includes session_cost_usd, so this is a backstop
            # that surfaces it explicitly for older clients.
            metadata["session_cost"] = float(getattr(TOKENS, "session_cost", 0.0) or 0.0)
            ui_state["session"].metadata = metadata
            # Save todos with session (store as metadata)
            ui_state["session"].todos = copy.deepcopy(ui_state["todos"]) if ui_state["todos"] else []
            SESSIONS.save(ui_state["session"])
            add_message('system', f'Session saved: {ui_state["session"].id} ({len(ui_state["todos"])} todos)')
            update_session_list()
        else:
            add_message('system', 'No session to save')

    def on_load(b):
        """Load selected session."""
        if ui_state.get("lock"):
            add_message('system', 'Agent is running. Stop it first.')
            return
        global _TODOS, _FILES_READ
        with _FILES_READ_LOCK:
            _FILES_READ.clear()
            _FILE_READ_TIMES.clear()  # V4: clear staleness tracking on session load
            _FILE_PARTIAL_READS.clear()  # V4.1 #10: clear partial view tracking
        session_id = session_dropdown.value
        if not session_id:
            # New session - just clear
            on_clear(None)
            return

        session = SESSIONS.load(session_id)
        if not session:
            add_message('system', f'Failed to load session: {session_id}')
            return

        # Restore saved model from session metadata when possible.
        saved_model = None
        if isinstance(session.metadata, dict):
            saved_model = session.metadata.get("model")
        if saved_model and saved_model in [m[1] for m in BEDROCK_MODELS] and saved_model != model_dropdown.value:
            ui_state["model_change_lock"] = True
            try:
                model_dropdown.value = saved_model
            finally:
                ui_state["model_change_lock"] = False
            try:
                ok, conn_msg = validate_model_connection(saved_model)
                if not ok:
                    raise RuntimeError(conn_msg)
                restored_client = BedrockClient(saved_model, CONFIG.region, CONFIG.mock_mode)
                CONFIG.model_id = saved_model
                ui_state["client"] = restored_client
                ui_state["model_connection_ok"] = True
                ui_state["model_connection_msg"] = conn_msg
                add_message('system', f'Restored model from session: {saved_model}')
            except Exception as e:
                ui_state["model_connection_ok"] = False
                ui_state["model_connection_msg"] = str(e)[:180]
                add_message('system', f'Failed to restore saved model {saved_model}: {str(e)[:120]}')

        # Refresh active model health so status line is always current after load.
        active_ok, active_msg = validate_model_connection(CONFIG.model_id)
        ui_state["model_connection_ok"] = active_ok
        ui_state["model_connection_msg"] = active_msg

        # Reset token counters (start fresh — saved stats kept in session JSON for history)
        TOKENS.reset()
        ui_state["session"] = session
        ui_state["agent"] = Agent(
            ui_state["client"],
            session.id,
            on_approval=request_approval,
            on_ask_user=request_user_input,
            on_tokens=lambda stats: update_tokens_display(),
            on_thinking=lambda t: add_message('thinking', t) if t else None,
            on_stop_check=lambda: ui_state.get("stop_requested", False),
            on_compact_fn=lambda: ui_state.get("always_allow", set()).clear(),  # V4.2 V2-D
        )
        ui_state["agent"].messages = copy.deepcopy(session.messages)
        if isinstance(session.metadata, dict):
            ui_state["agent"].user_msg_count = int(session.metadata.get("user_msg_count", 0) or 0)
            ui_state["agent"].exec_calls = int(session.metadata.get("exec_calls", 0) or 0)
            ui_state["agent"].exec_seconds = float(session.metadata.get("exec_seconds", 0.0) or 0.0)
            # V4.10.10 in-place: restore session_cost on the global TOKENS singleton
            # (Codex review caught the original mistake of writing to ui_state["agent"]).
            # The budget check at line 3635 and banner at line 3702 both read TOKENS.session_cost.
            # token_stats already restored via TOKENS.from_stats() if present, but a stale
            # session JSON without session_cost_usd would otherwise leave it at 0.0.
            _saved_cost = float(session.metadata.get("session_cost", 0.0) or 0.0)
            if _saved_cost > 0:
                TOKENS.session_cost = _saved_cost
            loaded_skills = session.metadata.get("active_skills", [])
            if isinstance(loaded_skills, list):
                ui_state["active_skills"] = [str(s) for s in loaded_skills if isinstance(s, str)]
            loaded_checkpoints = session.metadata.get("checkpoints", [])
            if isinstance(loaded_checkpoints, list):
                ui_state["checkpoints"] = copy.deepcopy(loaded_checkpoints)
            # Restore SKILLS.active_skill from loaded skills
            with SKILLS._pending_lock:
                if ui_state.get("active_skills"):
                    SKILLS.active_skill = ui_state["active_skills"][-1]
                else:
                    SKILLS.active_skill = None

        # Display loaded messages
        ui_state["messages"] = []
        add_message('system', f'Loaded session: {session.title} ({len(session.messages)} messages)')

        for msg in session.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                if isinstance(content, str):
                    add_message('user', content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            add_message('tool', item.get("content", "")[:200], "result")

            elif role == "assistant":
                if isinstance(content, str):
                    add_message('assistant', content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                add_message('assistant', item.get("text", ""))
                            elif item.get("type") == "tool_use":
                                add_message('tool', f'Called {item.get("name", "?")}', item.get("name"))

        # Restore todos from session (if saved)
        if hasattr(session, 'todos') and session.todos:
            _TODOS = copy.deepcopy(session.todos)
            ui_state["todos"] = copy.deepcopy(_TODOS)
            render_todos()
            add_message('system', f'Restored {len(_TODOS)} todos')
        else:
            _TODOS = []
            ui_state["todos"] = []
            render_todos()

        update_tokens_display()
        update_mode_display()

    def on_new(b):
        """Start a new session (clear current without saving)."""
        if ui_state.get("lock"):
            add_message('system', 'Agent is running. Stop it first.')
            return
        global _TODOS, _FILES_READ
        # V4.1 #8: Auto-extract memories at session end if enabled
        if ui_state["agent"]:
            _extract_and_append_memories(ui_state["agent"], output_fn=lambda m: add_message('system', m))
        if ui_state["agent"]:
            ui_state["agent"].reset()
        ui_state["agent"] = None
        _PENDING_IMAGES.clear()  # Clear any queued images
        ui_state["session"] = None
        _TODOS = []
        with _FILES_READ_LOCK:
            _FILES_READ.clear()
            _FILE_READ_TIMES.clear()  # V4: clear staleness tracking on new session
            _FILE_PARTIAL_READS.clear()  # V4.1 #10: clear partial view tracking
        TOKENS.reset()
        ui_state["messages"] = []
        ui_state["todos"] = []  # Clear todos
        ui_state["checkpoints"] = []
        ui_state["active_skills"] = []
        ui_state["deactivated_skills"] = set()  # V4.9.1: sticky deactivations don't carry across sessions
        with SKILLS._pending_lock:
            SKILLS.active_skill = None
            SKILLS._pending_activations.clear()
        render_chat()
        render_todos()  # Update todo display
        status_html.value = '<span style="color:#4caf50"><b>● Ready (New)</b></span>'
        update_tokens_display()
        update_mode_display()
        session_dropdown.value = None

    def on_compact(b):
        """Manually compact conversation context (2-stage)."""
        if not ui_state["agent"] or not ui_state["agent"].messages:
            add_message('system', 'No conversation to compact.')
            return

        # Lock is set by _on_compact_threaded wrapper before spawning this thread.
        compact_btn.disabled = True
        status_html.value = '<span style="color:#ff9800"><b>⋯ Compacting...</b></span>'

        try:
            messages = ui_state["agent"].messages
            original_count = len(messages)

            # Stage 1: Prune old tool outputs (2-stage)
            pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, CONFIG.context_max_tokens)
            if tokens_saved > 0:
                add_message('system', f'Stage 1: Pruned old tool outputs (~{tokens_saved:,} tokens saved)')
                ui_state["agent"].messages = pruned_msgs
                messages = pruned_msgs

            # Stage 2: LLM-generated summary (shared helper)
            add_message('system', 'Stage 2: Creating conversation summary...')

            summary = COMPACTOR.create_llm_summary(ui_state["client"], messages)

            if not summary:
                summary = "Conversation compacted (LLM summary unavailable). Continue from recent context."
                add_message('system', 'LLM summary failed, using fallback.')
            # Compact: keep summary + last 5 messages
            compacted = COMPACTOR.compact(messages, summary)
            ui_state["agent"].messages = compacted

            # Clear file dedup cache — compacted context no longer has old file reads
            FILE_CACHE.clear_context()
            # V4.2 V2-D: Expire stale "always approve" decisions — context was reset
            ui_state.get("always_allow", set()).clear()

            add_message('system', f'Compacted: {original_count} → {len(compacted)} messages')

            # Update context display
            usage = CONTEXT.get_usage(compacted)
            pct = usage["percent"] * 100
            add_message('system', f'Context now at {pct:.1f}% ({usage["tokens"]:,} tokens)')

        except Exception as e:
            add_message('system', f'Compact failed: {e}')
            import traceback
            traceback.print_exc()

        finally:
            ui_state["lock"] = False
            compact_btn.disabled = False
            status_html.value = '<span style="color:#4caf50"><b>● Ready</b></span>'
            update_tokens_display()

    def _on_send_threaded(b):
        """Run on_send in background thread so kernel thread stays free for widget events.
        Fixes: ask_user Submit/Skip buttons, Stop button, and approval dialogs all require
        the kernel thread to process click callbacks. Without threading, agent.run() blocks
        the kernel thread and creates a deadlock.

        Also acts as fallback for ask_user and approval dialogs: if the dedicated widget
        buttons (Submit/Skip/Approve/Deny) don't fire (e.g. SageMaker Studio comm issues),
        the user can type in the regular input box and press Send instead."""
        # Fallback: if ask_user is waiting, redirect Send input as the response
        if pending_user_input.get("event") and pending_user_input["result"] is None:
            val = input_box.value.strip() or "(no response)"
            input_box.value = ""
            pending_user_input["result"] = val
            pending_user_input["event"].set()
            return
        # Fallback: if approval is waiting, user must type "approve" or "yes" explicitly
        if pending_approval.get("event") and pending_approval["result"] is None:
            typed = input_box.value.strip().lower()
            input_box.value = ""
            if typed in ("approve", "yes", "y"):
                pending_approval["result"] = True
                pending_approval["event"].set()
            elif typed in ("deny", "no", "n"):
                pending_approval["result"] = False
                pending_approval["event"].set()
            else:
                add_message('system', 'Type "approve" or "deny" (or use the buttons above)')
            return
        if ui_state.get("lock"):
            return  # Agent already running
        ui_state["lock"] = True  # Set lock BEFORE spawning thread (atomic on kernel thread)
        threading.Thread(target=on_send, args=(b,), daemon=True).start()

    def _on_compact_threaded(b):
        """Run on_compact in background thread with lock pre-check."""
        if ui_state.get("lock"):
            return  # Agent already running
        ui_state["lock"] = True  # Set lock BEFORE spawning thread (atomic on kernel thread)
        threading.Thread(target=on_compact, args=(b,), daemon=True).start()

    def on_cleanup(b):
        """Delete local traces (keeps sessions for conversation continuity)."""
        if ui_state.get("lock"):
            add_message('system', 'Agent is running. Stop it first.')
            return
        import shutil as _shutil
        cleaned = []
        # Clean non-essential traces (sessions kept for continuity)
        for name, path in [
            ("audit_logs", CONFIG.audit_dir),
            (".snapshots", os.path.join(CONFIG.workspace, ".snapshots")),
            (".code_index", os.path.join(CONFIG.workspace, ".code_index")),
            ("truncated_outputs", os.path.join(CONFIG.workspace, "truncated_outputs")),
        ]:
            if os.path.isdir(path):
                _shutil.rmtree(path, ignore_errors=True)
                cleaned.append(name)
        # Also clean single files
        for name, path in [
            (".exec_budget.json", os.path.join(CONFIG.workspace, ".exec_budget.json")),
        ]:
            if os.path.isfile(path):
                os.unlink(path)
                cleaned.append(name)
        if cleaned:
            add_message('system', f'🧹 Cleaned: {", ".join(cleaned)} (sessions kept)')
        else:
            add_message('system', '🧹 Nothing to clean — no traces found.')
        render_chat()

    send_btn.on_click(_on_send_threaded)
    clear_btn.on_click(on_clear)
    save_btn.on_click(on_save)
    compact_btn.on_click(_on_compact_threaded)
    cleanup_btn.on_click(on_cleanup)
    load_btn.on_click(on_load)
    new_btn.on_click(on_new)

    # ========== BUILD LAYOUT ==========
    # CSS fix for Output widget scroll containment
    def get_header_html():
        c = get_colors()
        session_count = len(SESSIONS.list_sessions())
        return f'''
        <div style="border-bottom:1px solid {c['border']};padding-bottom:8px;margin-bottom:8px;">
            <h2 style="margin:0;color:#4a9eff;">SageMaker Coding Agent</h2>
            <p style="margin:4px 0;color:{c['fg_muted']};font-size:12px;">
                {len(TOOLS)} tools | {session_count} saved sessions | {CONFIG.region}
            </p>
        </div>
        '''

    header = widgets.HTML(get_header_html())
    # Store references for dark mode updates
    ui_state["header"] = header
    ui_state["get_header_html"] = get_header_html
    ui_state["update_tokens"] = update_tokens_display

    # === LAYOUT v2 ===
    # Grouped sections with visual separators. Status + metrics at bottom.
    #
    # ┌─ Header ─────────────────────────────────────────────────┐
    # │  SageAgent V4  |  22 tools  |  ap-southeast-2            │
    # ├─ Model & Controls ───────────────────────────────────────┤
    # │  [Model ▼]  [⚙ Sub-Agents ▶]                            │
    # │  [☑ Approval]  [☑ Dark Mode]  [Plan Mode]  [Auto-Compact]│
    # ├─ Thinking ───────────────────────────────────────────────┤
    # │  [☐ Extended Thinking]  [── Budget ──]  [── Temp ──]     │
    # ├─ Session ────────────────────────────────────────────────┤
    # │  [name___]  [💾 Save]  [▼ sessions]  [📂 Load]  [+ New] │
    # ├─ Chat ───────────────────────────────────────────────────┤
    # │  (conversation)                                          │
    # │  [Type your message...                                  ]│
    # │  [✈ Send] [■ Stop] [🗑 Clear]    [🔧 Compact] [🧹 Clean]│
    # ├─ Metrics & Status ───────────────────────────────────────┤
    # │  ▓▓░░░░░░ 14% context | In: 48K | Out: 1K | $0.06      │
    # │  Model: connected | Plan: OFF | Skills: 0 | Cost: $0.06│
    # └─────────────────────────────────────────────────────────┘

    _sep = widgets.HTML('<hr style="margin:4px 0;border:none;border-top:1px solid #333;"/>')
    _sep2 = widgets.HTML('<hr style="margin:4px 0;border:none;border-top:1px solid #333;"/>')
    _sep3 = widgets.HTML('<hr style="margin:4px 0;border:none;border-top:1px solid #333;"/>')
    _sep4 = widgets.HTML('<hr style="margin:2px 0;border:none;border-top:1px solid #333;"/>')

    # Group 1: Model + Mode + Approval (primary controls, left-aligned like session row)
    model_dropdown.description = ''
    model_dropdown.layout = widgets.Layout(width='260px')
    model_row = widgets.HBox([model_dropdown, _sa_toggle, plan_mode_toggle, approval_checkbox])
    model_row.layout = widgets.Layout(flex_flow='row wrap', align_items='center', gap='4px 8px')

    # Group 2: Thinking + budget + secondary toggles
    thinking_row = widgets.HBox([thinking_checkbox, thinking_budget_slider, temp_slider, budget_slider, auto_compact_checkbox, dark_mode_checkbox, chat_height_slider])
    thinking_row.layout = widgets.Layout(flex_flow='row wrap', align_items='center', gap='4px 8px')

    # Group 3: Session
    session_row = widgets.HBox([session_name_input, save_btn, session_dropdown, load_btn, new_btn])
    session_row.layout = widgets.Layout(flex_flow='row wrap', align_items='center', gap='4px 8px')

    # Action buttons: primary left, utility right
    action_left = widgets.HBox([send_btn, stop_btn, clear_btn])
    action_left.layout = widgets.Layout(gap='4px')
    action_right = widgets.HBox([compact_btn, cleanup_btn, status_html])
    action_right.layout = widgets.Layout(gap='4px')
    action_row = widgets.HBox([action_left, action_right])
    action_row.layout = widgets.Layout(justify_content='space-between', width='100%')

    # Full UI layout — session first (first action), config second, chat main, metrics bottom
    ui = widgets.VBox([
        header,
        # ── Session (first action: load/new/save) ──
        session_row,
        _sep,
        # ── Model + Plan + Approval (primary) ──
        model_row,
        _sa_panel,
        _sep2,
        # ── Thinking + Auto-Compact + Dark Mode (secondary) ──
        thinking_row,
        _sep3,
        # ── Chat area (95% of time here) ──
        todo_display,
        chat_display,
        approval_box,
        ask_user_box,
        input_box,
        action_row,
        _sep4,
        # ── Metrics & Status (reference, bottom) ──
        tokens_html,
        mode_html,
    ])

    update_session_list()
    update_tokens_display()
    # Validate initial model once so status line reflects real connectivity.
    init_ok, init_msg = validate_model_connection(CONFIG.model_id)
    ui_state["model_connection_ok"] = init_ok
    ui_state["model_connection_msg"] = init_msg
    update_mode_display()

    # Initialize displays
    render_chat()
    render_todos()

    try:
        display(ui)
    except UnicodeEncodeError:
        # Some Windows terminals use cp1252 and fail on widget/unicode rendering.
        print("UI created. Open this in Jupyter/Studio to render widgets.")
    return None  # Don't return ui - Jupyter would display it twice


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("SageMaker Coding Agent")
    print(f"  Region: {CONFIG.region}")
    print(f"  Model: {CONFIG.model_id}")
    print(f"  Tools: {len(TOOLS)}")
    print(f"  Mock mode: {CONFIG.mock_mode}")
    print("\nTo use in Jupyter:")
    print("  from sagemaker_agent import create_chat_ui")
    print("  create_chat_ui()")