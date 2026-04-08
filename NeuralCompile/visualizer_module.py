"""
visualizer_module.py - Line-by-line Python Tutor-style execution visualizer.
Includes ExecutionTracer, VisualizerState, and visualizer_page UI.
"""
import asyncio
import io
import re
import json
import html as _html
from typing import Any

import reflex as rx
from reflex_monaco.monaco import MonacoEditor
from .models import HistoryEntry
from .fingerprint import DeviceState
from .components import navbar, footer
from .cfg_generator import generate_cfg


# ── CFG iframe builder (shared logic) ─────────────────────────────────────────
_CFG_TEMPLATE = """<!DOCTYPE html><html><head>
<script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>
<link href='https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap' rel='stylesheet'>
<style>
  html,body{{margin:0;padding:0;width:100%;height:100%;background:#0d1117;overflow:hidden}}
  #g{{width:100%;height:100%;background:transparent}}
</style>
</head><body><div id='g'></div><script>
var data={cfg_json};
var colorMap={{
  statement:    {{bg:'rgba(107,115,255,0.85)',border:'#6B73FF',text:'#ffffff'}},
  condition:    {{bg:'rgba(151,71,255,0.85)', border:'#9747FF',text:'#ffffff'}},
  loop_guard:   {{bg:'rgba(227,98,9,0.85)',   border:'#E36209',text:'#ffffff'}},
  function_def: {{bg:'rgba(9,105,218,0.85)',  border:'#0969DA',text:'#ffffff'}},
  class_def:    {{bg:'rgba(210,168,255,0.85)',border:'#D2A8FF',text:'#ffffff'}},
  return:       {{bg:'rgba(207,34,46,0.85)',  border:'#CF222E',text:'#ffffff'}}
}};
var nodes=data.nodes.map(function(n){{
  var s=colorMap[n.type]||{{bg:'rgba(68,68,68,0.85)',border:'#555',text:'#ffffff'}};
  return {{id:n.id,label:n.label,lineno:n.lineno,
    color:{{background:s.bg,border:s.border,highlight:{{background:'rgba(107,115,255,0.85)',border:'#6B73FF'}}}},
    font:{{color:s.text,size:13,face:'JetBrains Mono'}},
    shape:'box',margin:14,borderWidth:2,shadow:{{enabled:true,color:'rgba(107,115,255,0.2)',size:8}}
  }};
}});
var edges=data.edges.map(function(e){{
  return {{from:e.source,to:e.target,label:e.label||'',arrows:'to',
    color:{{color:'rgba(107,115,255,0.5)',highlight:'#9747FF'}},
    font:{{color:'#8b949e',size:10,align:'top',face:'JetBrains Mono'}},width:2,
    smooth:{{type:'cubicBezier',roundness:0.4}}
  }};
}});
var network=new vis.Network(document.getElementById('g'),{{nodes:new vis.DataSet(nodes),edges:new vis.DataSet(edges)}},{{
  layout:{{
    hierarchical:{{
      enabled: true,
      direction:'UD',
      sortMethod:'directed',
      levelSeparation:120,
      nodeSpacing:200,
      treeSpacing:250,
      blockShifting: true,
      edgeMinimization: true,
      parentCentralization: true
    }}
  }},
  physics:{{
    enabled:false,
    stabilization: {{iterations: 1000}}
  }},
  edges: {{
    smooth: {{type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5}},
    arrows: {{to: {{enabled: true, scaleFactor: 0.8}}}}
  }},
  interaction:{{zoomView:true,dragView:true,hover:true}}
}});
network.once('stabilizationIterationsDone',function(){{network.fit({{animation:{{duration:400,easingFunction:'easeInOutQuad'}}}});}});
window.addEventListener('message',function(ev){{
  if(ev.data&&ev.data.type==='highlight_cfg'){{
    var n=nodes.find(function(x){{return x.lineno==ev.data.lineno;}});
    if(n){{network.selectNodes([n.id]);network.focus(n.id,{{scale:1.1,animation:true}});}}
  }}
}});
</script></body></html>"""


def _build_cfg_iframe(cfg_data: dict, height: str = "100%") -> str:
    if not cfg_data or cfg_data.get("error"):
        err = (cfg_data or {}).get("error", "CFG unavailable")
        return f"<div style='padding:16px;color:#ff7b72;font-family:JetBrains Mono;font-size:13px;'>⚠ {err}</div>"
    inner = _CFG_TEMPLATE.format(cfg_json=json.dumps(cfg_data))
    import html as _html
    safe = _html.escape(inner, quote=True)
    return (
        f"<iframe srcdoc='{safe}' "
        f"style='width:100%;height:{height};border:none;"
        f"border-radius:10px;background:var(--navbar-bg);display:block;'>"
        f"</iframe>"
    )


# ── Execution Tracer ──────────────────────────────────────────────────────────
class ExecutionTracer:
    def __init__(self):
        self.trace_data: list[dict[str, Any]] = []
        self.stdout_buffer = io.StringIO()
        self.code_string = ""

    def _clean_locals(self, local_vars: dict) -> dict:
        """Filter out built-ins and un-serializeable objects from locals."""
        clean = {}
        for k, v in local_vars.items():
            if k.startswith("__"):
                continue
            if isinstance(v, (int, float, str, bool, type(None))):
                clean[k] = v
            elif isinstance(v, (list, dict, tuple, set)):
                try:
                    clean[k] = repr(v)
                except Exception:
                    clean[k] = "<Unserializable>"
            else:
                 clean[k] = repr(v)
        return clean

    def _trace_calls(self, frame, event, arg):
        if frame.f_code.co_filename != "<string>":
            return None

        if event == 'line':
            line_no = frame.f_lineno
            locals_dict = self._clean_locals(frame.f_locals)
            current_stdout = self.stdout_buffer.getvalue()
            
            self.trace_data.append({
                "step": len(self.trace_data),
                "line": line_no,
                "func_name": frame.f_code.co_name,
                "locals": locals_dict,
                "stdout": current_stdout,
                "event": event
            })
        return self._trace_calls

    def trace_code(self, code: str) -> list[dict[str, Any]]:
        import sys, contextlib
        self.code_string = code
        self.trace_data = []
        self.stdout_buffer = io.StringIO()
        error_msg = None

        try:
            compiled_code = compile(code, "<string>", "exec")
        except SyntaxError as e:
            return [{
                "step": 0, "line": getattr(e, 'lineno', 1), 
                "locals": {}, "stdout": "", "event": "error", 
                "func_name": "error", "error": f"SyntaxError: {str(e)}"
            }]

        exec_globals = {"__name__": "__main__"}
        orig = sys.gettrace()
        sys.settrace(self._trace_calls)
        try:
            with contextlib.redirect_stdout(self.stdout_buffer):
                exec(compiled_code, exec_globals)
        except Exception as e:
             error_msg = f"{type(e).__name__}: {str(e)}"
        finally:
            sys.settrace(orig)

        final_stdout = self.stdout_buffer.getvalue()
        last_line = self.trace_data[-1]["line"] if self.trace_data else 1
        last_locals = self.trace_data[-1]["locals"] if self.trace_data else {}
        
        final_step = {
            "step": len(self.trace_data),
            "line": last_line,
            "locals": last_locals,
            "stdout": final_stdout,
            "event": "exception" if error_msg else "return",
            "func_name": "main"
        }
        if error_msg:
             final_step["error"] = error_msg
        self.trace_data.append(final_step)
        return self.trace_data


# ── VisualizerState ───────────────────────────────────────────────────────────
def _safe_json(raw: str, is_list=False):
    raw = raw.strip()
    # Remove markdown blocks
    if "```" in raw:
        try: raw = raw.split("```")[1].replace("json", "").strip()
        except: pass
    
    try: return json.loads(raw)
    except:
        start_char = "[" if is_list else "{"
        start_idx = raw.find(start_char)
        if start_idx != -1:
            cand = raw[start_idx:]
            # Simple cleanup for common LLM artifacts
            cand = cand.replace("'", '"').replace("True", "true").replace("False", "false").replace("None", "null")
            
            stack = []
            for i, c in enumerate(cand):
                if c in "{[":
                    stack.append(c)
                elif c in "}]":
                    if stack:
                        if (c == "}" and stack[-1] == "{") or (c == "]" and stack[-1] == "["):
                            stack.pop()
                if not stack:
                    try: return json.loads(cand[:i+1])
                    except: break
            
            # Healing truncated JSON
            if stack:
                healed = cand
                for s in reversed(stack):
                    healed += "}" if s == "{" else "]"
                try: return json.loads(healed)
                except: pass

        raise ValueError("JSON matching/recovery failed")


class VisualizerState(rx.State):
    code: str = "# Write your Python code here...\n\nprint('Hello, Neural Compile!')"
    language: str = "python"
    editor_theme: str = "vs-dark"
    update_version: int = 0
    supported_languages: list[str] = ["python", "javascript", "typescript", "c", "cpp", "java"]
    supported_themes: list[str] = ["vs-dark", "vs", "hc-black", "hc-light"]

    steps: list[dict] = []
    current_step_index: int = 0
    is_generating: bool = False
    is_playing: bool = False
    playback_speed: float = 1.0
    cfg_html: str = ""
    execution_timestamp: str = ""
    code_lines: list[str] = []
    ai_explanation: str = ""

    @rx.var
    def current_step(self) -> dict:
        if not self.steps:
            return {"line": 1, "locals": {}, "stdout": "", "func_name": "main", "event": "start", "error": ""}
        return self.steps[min(self.current_step_index, len(self.steps) - 1)]

    @rx.var
    def current_line(self) -> int:
        try:
            return int(self.current_step.get("line", 1))
        except (ValueError, TypeError):
            return 1

    @rx.var
    def locals_str(self) -> str:
        """Safely formats the locals dictionary into a readable string on the backend."""
        locs = self.current_step.get("locals", {})
        if not locs:
            return "{}"
        if isinstance(locs, str):
            return locs
        import json
        try:
            return json.dumps(locs, indent=2)
        except Exception:
            return str(locs)

    def set_code(self, val: str):
        self.code = val

    def set_language(self, lang: str):
        self.language = lang
        self.update_version += 1

    def set_editor_theme(self, theme: str):
        self.editor_theme = theme

    def set_step_index(self, val: list):
        self.current_step_index = int(val[0])

    def reset_visualizer(self):
        self.steps = []
        self.current_step_index = 0
        self.cfg_html = ""
        self.is_playing = False
        self.update_version += 1

    def next_step(self):
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1

    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1

    async def play_steps(self):
        if self.is_playing: return
        self.is_playing = True
        yield rx.console_log("🎬 Playback started.")
        
        while self.is_playing and self.current_step_index < len(self.steps) - 1:
            # High-frequency polling for 'is_playing' state to ensure instant Pause
            total_sleep = 0
            poll_interval = 0.1
            while total_sleep < self.playback_speed:
                await asyncio.sleep(min(poll_interval, self.playback_speed - total_sleep))
                if not self.is_playing: 
                    yield rx.console_log("⏸ Interrupted during sleep.")
                    return
                total_sleep += poll_interval
            
            if not self.is_playing: break
            self.current_step_index += 1
            yield
            
        self.is_playing = False
        yield rx.console_log("🛑 Playback stopped/finished.")

    async def stop_playback(self):
        self.is_playing = False
        yield rx.console_log("⏸ Pause requested.")

    def set_playback_speed(self, val: list):
        self.playback_speed = float(val[0])



    async def generate_steps(self):
        if not self.code.strip() or self.is_generating:
            return
        self.is_generating = True
        self.steps = []
        self.cfg_html = ""
        self.current_step_index = 0
        self.code_lines = self.code.splitlines()
        yield

        loop = asyncio.get_event_loop()

        if self.language == "python":
            tracer = ExecutionTracer()
            self.steps = await loop.run_in_executor(None, tracer.trace_code, self.code)
            cfg_data = await loop.run_in_executor(None, generate_cfg, self.code)
            self.cfg_html = _build_cfg_iframe(cfg_data, height="100%")
        else:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                from langchain_groq import ChatGroq
                import os
                llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
                
                # 1. Generate execution trace steps (Compiler-like fidelity)
                trace_prompt = f"""Simulate line-by-line execution of this {self.language} code like a high-fidelity compiler/CPU.
Return a RAW JSON list of steps. 
YOU MUST SIMULATE ALL LOOP ITERATIONS faithfully. Do not skip steps.

EACH STEP MUST FOLLOW THIS SCHEMA:
{{"line": <line_number_int>, "locals": {{"var_name": "value"}}, "stdout": "last printed", "func_name": "function_active", "event": "line"}}

Instructions:
1. Map every variable change in 'locals'.
2. Append to 'stdout' only when a print occurs.
3. Show the loop entering, EACH iteration, and the exit.
4. If there are infinite loops, cap at 30 steps.

Max 30 steps. Return ONLY the JSON list. No talking.
Code:
{self.code}"""
                trace_resp = await loop.run_in_executor(None, lambda: llm.invoke(trace_prompt).content)
                try:
                    self.steps = _safe_json(trace_resp, is_list=True)
                except Exception as e:
                    self.steps = [{"line": 1, "locals": {"error": f"AI Trace Parse Error: {str(e)}"}, "stdout": "", "func_name": "main", "event": "error"}]

                # 2. Generate CFG for this non-Python code
                lang_guidance = ""
                if self.language == "java":
                    lang_guidance = "Focus on the entry point (public static void main). Map class structure and method boundaries clearly."
                elif self.language == "typescript":
                    lang_guidance = "Include arrow functions, async/await blocks, and handle exported function flows."

                cfg_prompt = f"""Generate a high-fidelity Control Flow Graph (CFG) for this {self.language} code.
{lang_guidance}
Return a RAW JSON structure strictly matching this schema:
{{
  "nodes": [ {{"id": 0, "label": "L1: x=10", "type": "statement", "lineno": 1}}, ... ],
  "edges": [ {{"from": 0, "to": 1, "label": "next"}}, ... ]
}}
Return ONLY the JSON. No explanations.
Code:
{self.code}"""
                cfg_resp = await loop.run_in_executor(None, lambda: llm.invoke(cfg_prompt).content)
                try:
                    cfg_data = _safe_json(cfg_resp)
                    self.cfg_html = _build_cfg_iframe(cfg_data, height="100%")
                except:
                    self.cfg_html = ""
            except Exception as e:
                self.steps = [{"line": 1, "locals": {"error": str(e)}, "stdout": "", "func_name": "error", "event": "error"}]

        # Save history
        device_state = await self.get_state(DeviceState)
        uuid = device_state.safe_uuid
        with rx.session() as session:
            session.add(HistoryEntry(
                device_uuid=uuid,
                title=f"Visualize: {self.language}",
                code=self.code[:2000],
                result=f"Traced {len(self.steps)} steps.",
                language=self.language,
                category="visualizer",
            ))
            session.commit()

        import datetime
        self.execution_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.is_generating = False
        yield


# ── visualizer_page UI ────────────────────────────────────────────────────────
def code_execution_view(state: VisualizerState):
    def render_line(line, index):
        # Comparison with integer line number
        is_active = (index + 1) == state.current_step["line"]
        
        return rx.hstack(
            rx.box(
                rx.icon("chevron-right", size=16, color="#3fb950"),
                width="20px",
                display="flex",
                justify_content="center",
                visibility=rx.cond(is_active, "visible", "hidden")
            ),
            rx.text(
                (index + 1).to(str),
                width="30px",
                font_family="'JetBrains Mono', monospace",
                font_size="12px",
                color="var(--iris-8)",
                opacity="0.5",
                text_align="right",
                padding_right="8px"
            ),
            rx.text(
                line,
                font_family="JetBrains Mono",
                font_size="14px",
                white_space="pre",
                color=rx.cond(is_active, "#ffffff", "var(--text-color)")
            ),
            width="100%",
            padding_y="2px",
            background=rx.cond(is_active, "rgba(46, 160, 67, 0.15)", "transparent"),
            border_left=rx.cond(is_active, "4px solid #3fb950", "4px solid transparent"),
            align="center",
            spacing="0",
        )

    return rx.scroll_area(
        rx.vstack(
            rx.foreach(
                state.code_lines,
                lambda line, index: render_line(line, index)
            ),
            width="100%",
            spacing="0",
            padding_y="10px",
        ),
        height="100%",
        width="100%",
    )

def visualizer_page():
    return rx.vstack(
        navbar(active_page="Visualizer"),
        rx.vstack(
            rx.badge("🎬 Neural Tutor", color_scheme="amber"),
            rx.heading("Line-by-Line Execution Visualizer", size="7"),
            rx.text("Step through code execution to see variable states and control flow in real time.", color="gray"),

            rx.hstack(
                rx.text("Language:", font_weight="600"),
                rx.select(
                    VisualizerState.supported_languages,
                    value=VisualizerState.language,
                    on_change=VisualizerState.set_language,
                    width="110px", size="1", variant="soft",
                ),
                rx.text("Theme:", font_weight="600"),
                rx.select(
                    VisualizerState.supported_themes,
                    value=VisualizerState.editor_theme,
                    on_change=VisualizerState.set_editor_theme,
                    width="90px", size="1", variant="soft",
                ),
                rx.spacer(),
                rx.button(rx.icon("rotate-ccw", size=14), "Reset",
                          on_click=VisualizerState.reset_visualizer, variant="outline", size="2"),
                rx.button(rx.icon("play", size=14), "Generate Steps",
                          on_click=VisualizerState.generate_steps,
                          color_scheme="amber", size="2",
                          is_loading=VisualizerState.is_generating),
                width="100%", align="center", padding_y="8px",
            ),

            rx.hstack(
                # Left: Editor or Execution View
                rx.box(
                    rx.cond(
                        VisualizerState.steps,
                        code_execution_view(VisualizerState),
                        rx.cond(
                            VisualizerState.is_hydrated,
                            rx.box(
                                MonacoEditor.create(
                                    key=f"visualizer-{VisualizerState.update_version}",
                                    height="100%",
                                    language=VisualizerState.language,
                                    default_value=VisualizerState.code,
                                    theme=VisualizerState.editor_theme,
                                    on_change=VisualizerState.set_code,
                                    options={
                                        "fontSize": 14, "minimap": {"enabled": False},
                                        "automaticLayout": True, "scrollBeyondLastLine": False,
                                        "glyphMargin": True, "lineNumbersMinChars": 3,
                                        "fontLigatures": True,
                                    },
                                ),
                                height="100%", width="100%"
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.spinner(size="3"),
                                    rx.text("Connecting to Neural Engine...", font_size="14px", color="rgba(255,255,255,0.4)"),
                                    align="center", spacing="3"
                                ),
                                width="100%", height="100%", background="rgba(0,0,0,0.1)"
                            )
                        )
                    ),
                    width="30%", height="100%",
                    border="1px solid #30363d", border_radius="10px", overflow="hidden",
                    background="var(--navbar-bg)",
                ),

                # Right: Controls + CFG
                rx.vstack(
                    # Playback controls
                    rx.hstack(
                        rx.button(rx.icon("chevron-left"), on_click=VisualizerState.prev_step,
                                  variant="outline", size="2"),
                        rx.cond(
                            VisualizerState.is_playing,
                            rx.button(rx.icon("pause"), on_click=VisualizerState.stop_playback,
                                      color_scheme="red", size="2"),
                            rx.button(rx.icon("play"), on_click=VisualizerState.play_steps,
                                      color_scheme="green", size="2"),
                        ),
                        rx.button(rx.icon("chevron-right"), on_click=VisualizerState.next_step,
                                  variant="outline", size="2"),
                        rx.hstack(
                            rx.text((VisualizerState.current_step_index + 1).to(str), font_size="12px", font_family="JetBrains Mono"),
                            rx.text(" / ", font_size="12px", font_family="JetBrains Mono"),
                            rx.cond(
                                VisualizerState.steps,
                                rx.text(VisualizerState.steps.to(list).length().to(str), font_size="12px", font_family="JetBrains Mono"),
                                rx.text("1", font_size="12px", font_family="JetBrains Mono")
                            ),
                            spacing="1", align="center"
                        ),
                        spacing="3", align="center", width="100%",
                        padding="10px",
                        background="var(--bg-color)",
                        border="1px solid #30363d", border_radius="8px",
                    ),

                    # Variable state
                    rx.vstack(
                        rx.vstack(
                            rx.text("Line ", VisualizerState.current_line.to(str), font_weight="bold", font_size="12px"),
                            rx.spacer(),
                            rx.text("Function: ", VisualizerState.current_step["func_name"].to(str), font_size="12px", color="gray"),
                            align="start", spacing="0"
                        ),
                        rx.box(
                            rx.cond(
                                VisualizerState.current_step["error"],
                                rx.text(
                                    "❌ ERROR: ", VisualizerState.current_step["error"].to(str), 
                                    font_family="'JetBrains Mono', monospace",
                                    font_size="12px", white_space="pre-wrap", color="#ff7b72",
                                    margin_bottom="8px"
                                ),
                            ),
                            rx.text(
                                VisualizerState.locals_str,
                                font_family="'JetBrains Mono', monospace",
                                font_size="12px", white_space="pre-wrap", color="var(--text-color)"
                            ),
                            rx.cond(
                                VisualizerState.ai_explanation != "",
                                rx.box(
                                    rx.markdown(VisualizerState.ai_explanation.to(str)),
                                    width="100%", padding="15px", background="rgba(107,115,255,0.05)", border_radius="10px",
                                    margin_top="10px"
                                ),
                            ),
                            width="100%", max_height="150px", overflow_y="auto",
                            padding="8px", background="var(--card-bg)", border_radius="6px",
                        ),
                        width="100%", spacing="2",
                        padding="10px",
                        border="1px solid #30363d", border_radius="8px",
                        background="rgba(0,0,0,0.3)",
                    ),

                    # stdout
                    rx.vstack(
                        rx.hstack(rx.icon("terminal", size=14, color="#7ee787"),
                                  rx.text("Output", font_weight="700", size="2"), width="100%"),
                        rx.box(
                            rx.vstack(
                                rx.text(VisualizerState.current_step["stdout"].to(str),
                                        font_family="'JetBrains Mono', monospace",
                                        font_size="12px", white_space="pre-wrap", color="var(--text-color)",
                                        width="100%"),
                                rx.cond(
                                    VisualizerState.current_step["stdout"] != "",
                                    rx.hstack(
                                        rx.text("Stepped at: ", VisualizerState.execution_timestamp, color="gray", size="1"),
                                        rx.spacer(),
                                        rx.button(
                                            rx.icon("copy", size=14), "Copy Output",
                                            on_click=rx.set_clipboard(VisualizerState.current_step["stdout"]),
                                            size="1", variant="ghost", color_scheme="gray"
                                        ),
                                        width="100%", align="center", border_top="1px solid var(--border-color)", padding_top="8px", margin_top="8px"
                                    )
                                ),
                            ),
                            width="100%", min_height="50px", padding="8px",
                            background="var(--card-bg)", border_radius="6px",
                        ),
                        width="100%", spacing="2",
                        padding="10px",
                        border="1px solid #30363d", border_radius="8px",
                    ),

                    # CFG
                    rx.cond(
                        VisualizerState.cfg_html != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("git-branch", size=14, color="#6B73FF"),
                                rx.text("Control Flow Graph", font_weight="700", size="2"),
                                width="100%",
                            ),
                            rx.box(
                                rx.html(VisualizerState.cfg_html),
                                height="100%", width="100%", flex="1",
                                style={"overflow": "auto"}
                            ),
                            width="100%", flex="1", height="80vh",
                            padding="10px", spacing="2",
                            border="1px solid #30363d", border_radius="8px",
                            display="flex", flex_direction="column",
                        ),
                    ),

                    width="70%",
                    height="100%",
                    overflow_y="auto",
                    spacing="3",
                ),

                width="100%",
                height="calc(100vh - 280px)",
                align="stretch",
                spacing="4",
            ),

            width="100%",
            padding_x="32px",
            align="center",
            spacing="3",
            padding_top="20px",
            class_name="page-content",
        ),
        footer(),
        width="100%",
        min_height="100vh",
        background_color="var(--bg-color)",
    )
