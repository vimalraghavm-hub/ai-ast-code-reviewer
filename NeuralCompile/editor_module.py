"""
editor_module.py - Neural IDE, CFG integration, Neural Tutor visualizer, AI analysis.
Restricted to: Python, Javascript, Typescript, Java, C++.
"""
import asyncio
import re
import os
import tempfile
import subprocess
import json
import html as _html
from datetime import datetime

import reflex as rx
from reflex_monaco.monaco import MonacoEditor

from .models import HistoryEntry
from .fingerprint import DeviceState
from .components import navbar, footer
from .cfg_generator import generate_cfg

import pydantic

# ── Language Samples ────────────────────────────────────────────────────────
LANGUAGE_SAMPLES = {
    "python": "\"\"\"\nNeural Compile - Python Sample\nStandard Library Support: math, os, json, re, datetime, etc.\n\"\"\"\nimport math\n\ndef calculate_radius(area):\n    return math.sqrt(area / math.pi)\n\nprint(f'Radius for area 100: {calculate_radius(100):.2f}')\nprint('System Check: Standard libraries active.')",
    "javascript": "/*\nNeural Compile - JavaScript (Node.js) Sample\nStandard Node.js modules supported.\n*/\nconst fs = require('fs');\nconst path = require('path');\n\nconst greeting = 'Hello, Neural Compile!';\nconsole.log(greeting);\nconsole.log(`Working Directory: ${process.cwd()}`);",
    "typescript": "/*\nNeural Compile - TypeScript Sample\nType-safe code analysis integrated.\n*/\ninterface User {\n    id: number;\n    name: string;\n}\n\nfunction greet(user: User): string {\n    return `Welcome, ${user.name}! (ID: ${user.id})`;\n}\n\nconst newUser: User = { id: 101, name: 'Neural' };\nconsole.log(greet(newUser));",
    "java": "/*\nNeural Compile - Java Sample\nCompilation support: JDK 17+\n*/\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Neural Compile from Java!\");\n        double result = Math.pow(2, 10);\n        System.out.println(\"2^10 = \" + result);\n    }\n}",
    "c": "/*\nNeural Compile - C Sample\nCompilation support: GCC\n*/\n#include <stdio.h>\n\nint main() {\n    printf(\"Hello, Neural Compile from C!\\n\");\n    int numbers[] = {1, 2, 3, 4, 5};\n    int sum = 0;\n    for(int i = 0; i < 5; i++) {\n        sum += numbers[i];\n    }\n    printf(\"Sum of first 5 natural numbers: %d\\n\", sum);\n    return 0;\n}",
    "cpp": "/*\nNeural Compile - C++ Sample\nCompilation support: G++ / GCC\n*/\n#include <iostream>\n#include <vector>\n#include <cmath>\n\nint main() {\n    std::vector<std::string> tech = {\"Neural\", \"Compile\", \"IDE\"};\n    std::cout << \"System Launch: \";\n    for(const auto& t : tech) {\n        std::cout << t << \" \";\n    }\n    std::cout << std::endl;\n    std::cout << \"Sqrt(64) = \" << sqrt(64) << std::endl;\n    return 0;\n}"
}

# ── Chat Logic ───────────────────────────────────────────────────────────────
class ChatMessage(pydantic.BaseModel):
    role: str
    content: str
    timestamp: str

class ChatState(rx.State):
    messages: list[ChatMessage] = []
    input_text: str = ""
    is_loading: bool = False
    show_chat: bool = False

    def toggle_chat(self):
        self.show_chat = not self.show_chat

    def set_input_text(self, text: str):
        self.input_text = text

    def set_show_chat(self, val: bool):
        self.show_chat = val

    def set_messages(self, val: list[ChatMessage]):
        self.messages = val

    def handle_chat_keydown(self, key: str):
        if key == "Enter":
            return ChatState.send_message

    async def send_message(self):
        if not self.input_text.strip() or self.is_loading: return
        
        user_text = self.input_text
        self.input_text = ""
        self.is_loading = True
        yield rx.call_script("document.getElementById('chat-input-area').value = ''")
        yield
        
        import datetime
        user_msg = ChatMessage(
            role="user", 
            content=user_text, 
            timestamp=datetime.datetime.now().strftime("%H:%M")
        )
        self.messages.append(user_msg)
        query = user_text
        # Input already cleared above

        editor_state = await self.get_state(EditorState)
        code_context = (
            f"Language: {editor_state.editor_language}\n"
            f"Code:\n{editor_state.editor_code}\n\n"
            f"Recent Execution Output:\n{editor_state.terminal_output}"
        )
        
        try:
            from langchain_groq import ChatGroq
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            key = os.getenv("GROQ_API_KEY")
            if not key: raise ValueError("GROQ_API_KEY not found.")
            key = key.strip('"').strip("'")

            llm = ChatGroq(model_name="llama-3.1-8b-instant", api_key=key)
            system_prompt = f"You are Neural AI, a helpful coding assistant for the 'Neural Compile' IDE. Context of current file:\n{code_context}\n\nProvide clear, helpful coding advice, explain concepts, or suggest improvements."
            msgs = [("system", system_prompt)]
            for m in self.messages[-10:]:
                msgs.append((m.role, m.content))
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: llm.invoke(msgs).content
            )
            
            ai_msg = ChatMessage(role="assistant", content=response, timestamp=datetime.datetime.now().strftime("%H:%M"))
            self.messages.append(ai_msg)
        except Exception as e:
            self.messages.append(ChatMessage(role="assistant", content=f"❌ Chat Error: {e}", timestamp="now"))
        
        self.is_loading = False
        yield rx.call_script("document.getElementById('chat-scroll-area').scrollTo({top: 1e9, behavior: 'smooth'})")

    def clear_chat(self):
        self.messages = []


# ── helper to build the CFG HTML iframe ───────────────────────────────────────
_CFG_HTML_TEMPLATE = """<!DOCTYPE html><html><head>
<script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  html,body{{margin:0;padding:0;width:100%;height:100%;background:#0d1117;overflow:hidden}}
  #g{{width:100%;height:100%;background:transparent}}
</style>
</head><body><div id='g'></div><script>
var data={cfg_json};
var colorMap={{
  statement:   {{bg:'rgba(107,115,255,0.85)',border:'#6B73FF',text:'#ffffff'}},
  condition:   {{bg:'rgba(151,71,255,0.85)', border:'#9747FF',text:'#ffffff'}},
  loop_guard:  {{bg:'rgba(227,98,9,0.85)',   border:'#E36209',text:'#ffffff'}},
  function_def:{{bg:'rgba(9,105,218,0.85)',  border:'#0969DA',text:'#ffffff'}},
  class_def:   {{bg:'rgba(210,168,255,0.85)',border:'#D2A8FF',text:'#ffffff'}},
  return:      {{bg:'rgba(207,34,46,0.85)',  border:'#CF222E',text:'#ffffff'}}
}};
var nodes=data.nodes.map(function(n){{
  var s=colorMap[n.type]||{{bg:'rgba(68,68,68,0.8)',border:'#555',text:'#ffffff'}};
  return {{id:n.id,label:n.label,lineno:n.lineno,
    color:{{background:s.bg,border:s.border,highlight:{{background:'rgba(107,115,255,0.85)',border:'#6B73FF'}}}},
    font:{{color:s.text,size:13,face:'JetBrains Mono'}},
    shape:'box',margin:14,borderWidth:2,
    shadow:{{enabled:true,color:'rgba(107,115,255,0.15)',size:8,x:2,y:2}}
  }};
}});
var edges=data.edges.map(function(e){{
  return {{from:e.source,to:e.target,
    label:e.label||'',arrows:'to',
    color:{{color:'rgba(107,115,255,0.5)',highlight:'#9747FF'}},
    font:{{color:'#8b949e',size:10,align:'top',face:'JetBrains Mono'}},
    width:2,smooth:{{type:'cubicBezier',roundness:0.4}}
  }};
}});
var opts={{
  layout:{{hierarchical:{{direction:'UD',sortMethod:'directed',levelSeparation:120,nodeSpacing:100}}}},
  physics:{{enabled:true,hierarchicalRepulsion:{{nodeDistance:200,avoidOverlap:1}},stabilization:{{iterations:200}}}},
  interaction:{{zoomView:true,dragView:true,hover:true,tooltipDelay:200}}
}};
var network=new vis.Network(document.getElementById('g'),{{nodes:new vis.DataSet(nodes),edges:new vis.DataSet(edges)}},opts);
network.once('stabilizationIterationsDone',function(){{network.fit({{animation:{{duration:400,easingFunction:'easeInOutQuad'}}}});}});
window.addEventListener('message',function(ev){{
  if(ev.data&&ev.data.type==='highlight_cfg'){{
    var n=nodes.find(function(x){{return x.lineno==ev.data.lineno;}});
    if(n){{network.selectNodes([n.id]);network.focus(n.id,{{scale:1.1,animation:true}});}}
  }}
}});
</script></body></html>"""


def build_cfg_iframe(cfg_data: dict, height: str = "100%") -> str:
    if not cfg_data or cfg_data.get("error"):
        err = cfg_data.get("error", "CFG unavailable") if cfg_data else "CFG unavailable"
        return f"<div style='padding:20px;color:#ff7b72;font-family:JetBrains Mono;'>⚠ {err}</div>"
    inner = _CFG_HTML_TEMPLATE.format(cfg_json=json.dumps(cfg_data))
    safe = _html.escape(inner, quote=True)
    # Use background: transparent and ensure 100% height
    return f"<iframe srcdoc='{safe}' style='width:100%;height:{height};border:none;border-radius:10px;background:transparent;display:block;'></iframe>"


def markdown_components(lang: str):
    return {
        "code": lambda value, inline=False: rx.cond(
            inline,
            rx.code(
                value, 
                font_size="13px", 
                padding="1px 4px", 
                background="rgba(107,115,255,0.15)",
                color="#7ee787", # Greenish for code contrast
                border="1px solid rgba(107,115,255,0.3)",
                border_radius="4px",
            ),
            rx.box(
                rx.code_block(
                    value,
                    theme="vs-dark",
                    language=lang,
                    show_line_numbers=False,
                    width="100%",
                    custom_style={"backgroundColor": "transparent", "padding": "0", "margin": "0"},
                ),
                rx.button(
                    rx.icon("copy", size=14),
                    on_click=rx.set_clipboard(value),
                    position="absolute", top="10px", right="10px",
                    size="1", variant="soft", color_scheme="blue",
                    z_index="10",
                ),
                class_name="neural-code-container",
                padding="40px 15px 15px 15px",
            ),
        ),
    }

# ── Execution helper ───────────────────────────────────────────────────────────
def _run_code_sync(code: str, language: str) -> str:
    lang = language.lower()
    if lang == "python":
        try:
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=10)
            return (result.stdout + result.stderr).strip() or "✅ Executed (no output)"
        except subprocess.TimeoutExpired: return "⏱ Execution timed out (10s)"
        except Exception as e: return f"❌ {e}"
    elif lang in ("java", "c", "cpp", "c++"):
        try:
            suffix = {"java": ".java", "c": ".c", "cpp": ".cpp", "c++": ".cpp"}.get(lang, ".cpp")
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w") as f:
                f.write(code)
                fname = f.name
            
            output_name = fname + ".out"
            compile_cmd = {
                "c": ["gcc", fname, "-o", output_name, "-lm"],
                "cpp": ["g++", "-std=c++17", fname, "-o", output_name],
                "c++": ["g++", "-std=c++17", fname, "-o", output_name],
                "java": ["javac", fname],
            }.get(lang, [])
            
            if compile_cmd:
                r = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
                if r.returncode != 0: 
                    return f"❌ Compile error ({lang}):\n{r.stderr}"
            
            # Execution
            if lang == "java":
                # For Java, find class name by filename (javac produces <name>.class)
                class_path = os.path.dirname(fname)
                class_name = os.path.basename(fname).replace(".java", "")
                res = subprocess.run(["java", "-cp", class_path, class_name], capture_output=True, text=True, timeout=10)
            else:
                res = subprocess.run([output_name], capture_output=True, text=True, timeout=10)
                
            return (res.stdout + res.stderr).strip() or "✅ Compiled & Executed (no output)"
        except subprocess.TimeoutExpired: return "⏱ Runtime timed out (10s)"
        except FileNotFoundError as e: return f"⚠ Compiler/Runtime not found: {e.filename}"
        except Exception as e: return f"❌ Runtime Error: {e}"
    elif lang in ("javascript", "typescript"):
        try:
            r = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=10)
            return (r.stdout + r.stderr).strip() or "✅ Executed (no output)"
        except FileNotFoundError: return "⚠ Node.js not found."
        except Exception as e: return f"❌ {e}"
    else: return f"ℹ Execution for {language} is supported via AI Analysis only."


def _analyze_code_sync(code: str, language: str) -> dict:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from langchain_groq import ChatGroq
        import os, json, re
        from .error_detector import get_python_score
        llm = ChatGroq(temperature=0.1, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
        prompt = f"""Review this {language} code for bugs, logic errors, and clean code violations.
**Requirements**:
1. **AI Optimization**: Provide an optimized version of the code that reduces time/space complexity.
2. If the code lacks a formal structure, suggest implementing it using **Classes** for modularity.
3. If there is no **Exception Handling**, suggest adding robust error detection (try/except blocks).
4. Provide a clear explanation of these improvements and optimizations.

Return a RAW JSON object with this exact structure:
{{
  "explanation": "Detailed markdown explanation of the issues and how to fix them.",
  "fixed_code": "The complete refined code block."
}}
Code:\n```{language}\n{code}\n```"""
        resp = llm.invoke(prompt).content
        res_dict = {"explanation": resp, "fixed_code": ""}
        # Robust extraction
        m = re.search(r"(\{.*\})", resp, re.DOTALL)
        if m:
            cand = m.group(1)
            d = 0
            for i, c in enumerate(cand):
                if c == "{": d += 1
                elif c == "}": d -= 1
                if d == 0:
                    try: 
                        res_dict = json.loads(cand[:i+1])
                        break
                    except: break
        
        # Scoring Integration
        ast_score = get_python_score(code) if language.lower() == "python" else 0
        final_score = ast_score if (language.lower() == "python" and ast_score > 0) else 75
        
        # Prepend score to explanation
        explanation = res_dict.get("explanation", "")
        if explanation:
            res_dict["explanation"] = f"### 📊 Final Quality Score: {final_score}/100\n\n" + explanation
            
        return res_dict
    except Exception as e: return {"explanation": f"❌ AI analysis failed: {e}", "fixed_code": ""}


class LogEntry(pydantic.BaseModel):
    timestamp: str
    category: str
    content: str

# ── EditorState ───────────────────────────────────────────────────────────────
class EditorState(rx.State):
    editor_code: str = LANGUAGE_SAMPLES["python"]
    editor_language: str = "python"
    editor_theme: str = "vs-dark"
    update_version: int = 0
    supported_languages: list[str] = ["python", "javascript", "typescript", "c", "cpp", "java"]
    supported_themes: list[str] = ["vs-dark", "vs", "hc-black", "hc-light"]
    terminal_output: str = "▶ Click RUN to execute your code."
    execution_timestamp: str = ""
    cfg_html: str = ""
    suggested_codes: list[str] = []
    ai_explanation: str = ""
    ai_fixed_code: str = ""
    is_ai_fixing: bool = False
    execution_logs: list[LogEntry] = []
    is_running: bool = False

    # Neural Tutor
    trace_steps: list[dict] = []
    current_step_index: int = 0
    is_visualizing: bool = False
    is_playing: bool = False
    playback_speed: float = 1.0

    @rx.var
    def current_step(self) -> dict:
        if not self.trace_steps: return {"line": "0", "vars": "{}", "stdout": "", "func_name": "main"}
        idx = min(self.current_step_index, len(self.trace_steps) - 1)
        return self.trace_steps[idx]

    def set_editor_code(self, code: str):
        self.editor_code = code

    def set_editor_language(self, lang: str):
        self.editor_language = lang
        if lang in LANGUAGE_SAMPLES:
            self.editor_code = LANGUAGE_SAMPLES[lang]
        self.update_version += 1

    def set_editor_theme(self, theme: str):
        self.editor_theme = theme
        
    def clear_terminal(self):
        self.terminal_output = ""
        self.is_running = False
        self.cfg_html = ""
        self.suggested_codes = []
        self.execution_logs = []

    def toggle_visualize(self):
        self.is_visualizing = False
        self.trace_steps = []
        self.current_step_index = 0

    def next_step(self):
        if self.current_step_index < len(self.trace_steps) - 1:
            self.current_step_index += 1

    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1

    async def set_step_index(self, val: list):
        self.current_step_index = int(val[0])

    async def play_steps(self):
        if self.is_playing: return
        self.is_playing = True
        yield rx.console_log("🎬 Visualizer playback started.")
        
        while self.is_playing and self.current_step_index < len(self.trace_steps) - 1:
            # High-frequency polling for 'is_playing' state to ensure instant Pause
            total_sleep = 0
            poll_interval = 0.1
            while total_sleep < self.playback_speed:
                await asyncio.sleep(min(poll_interval, self.playback_speed - total_sleep))
                if not self.is_playing:
                    yield rx.console_log("⏸ Tutor interrupted during sleep.")
                    return
                total_sleep += poll_interval

            if not self.is_playing: break
            self.current_step_index += 1
            yield
            
        self.is_playing = False
        yield rx.console_log("🛑 Visualizer playback stopped.")

    async def stop_playback(self):
        self.is_playing = False
        yield rx.console_log("⏸ Visualizer pause requested.")

    async def run_code(self):
        if self.is_running: return
        self.is_running = True
        self.execution_logs = [] 
        self.terminal_output = "⚡ Running..."
        self.cfg_html = ""
        yield
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, _run_code_sync, self.editor_code, self.editor_language)
        import datetime
        now_ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        self.execution_timestamp = now_ts
        self.terminal_output = output
        self.execution_logs.append(LogEntry(timestamp=now_ts, category=self.editor_language, content=output))
        if self.editor_language == "python":
            cfg_data = await loop.run_in_executor(None, generate_cfg, self.editor_code)
            self.cfg_html = build_cfg_iframe(cfg_data, height="100%")
        self.is_running = False

    async def generate_cfg_only(self):
        if self.is_running: return
        self.is_running = True
        self.cfg_html = "🔍 Generating CFG..."
        yield
        loop = asyncio.get_event_loop()
        if self.editor_language == "python":
            cfg_data = await loop.run_in_executor(None, generate_cfg, self.editor_code)
            self.cfg_html = build_cfg_iframe(cfg_data, height="100%")
        else:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                from langchain_groq import ChatGroq
                import os
                llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
                # Language-specific guidance for higher fidelity CFGs
                lang_guidance = ""
                if self.editor_language == "java":
                    lang_guidance = "Focus on the entry point (public static void main). Map class structure and method boundaries clearly."
                elif self.editor_language == "typescript":
                    lang_guidance = "Include arrow functions, async/await blocks, and handle exported function flows."
                
                cfg_prompt = f"""Generate a high-fidelity Control Flow Graph (CFG) for this {self.editor_language} code.
{lang_guidance}
Return a JSON structure MUST match this format:
{{
  "nodes": [ {{"id": 0, "label": "L1: ...", "type": "statement", "lineno": 1}}, ... ],
  "edges": [ {{"source": 0, "target": 1, "label": ""}}, ... ]
}}
Types: statement, condition, loop_guard, function_def, return.
Requirements:
1. Every node must be connected.
2. Use hierarchical, top-down control flow logic.
3. Label nodes with line numbers (e.g., L5: if (x > 0)).
Code:\n{self.editor_code}"""
                cfg_resp = await loop.run_in_executor(None, lambda: llm.invoke(cfg_prompt).content)
                def _safe_json(raw: str):
                    try:
                        raw = raw.strip()
                        # Find the first { and the corresponding balancing }
                        start = raw.find('{')
                        if start == -1: return {}
                        
                        depth = 0
                        for i in range(start, len(raw)):
                            if raw[i] == '{': depth += 1
                            elif raw[i] == '}': 
                                depth -= 1
                                if depth == 0:
                                    # Successfully found matched block
                                    return json.loads(raw[start:i+1])
                        return json.loads(raw[start:]) # Fallback
                    except Exception:
                        return {"error": "JSON Extraction failed"}

                cfg_match = re.search(r"(\{.*\})", cfg_resp, re.DOTALL)
                if cfg_match:
                    cfg_data = _safe_json(cfg_resp)
                    self.cfg_html = build_cfg_iframe(cfg_data, height="100%")
                else:
                    self.cfg_html = "⚠ AI CFG Parse failed."
            except Exception as e:
                self.cfg_html = f"⚠ AI CFG Error: {str(e)}"
        self.is_running = False

    async def visualize_code(self):
        if self.is_running: return
        self.is_running = True
        self.is_visualizing = True
        self.execution_logs = []  # Clear previous output
        self.terminal_output = "🎬 Generating execution trace..."
        self.current_step_index = 0
        yield
        loop = asyncio.get_event_loop()
        if self.editor_language == "python":
            from .visualizer_module import ExecutionTracer
            tracer = ExecutionTracer()
            self.trace_steps = await loop.run_in_executor(None, tracer.trace_code, self.editor_code)
        else:
            # AI Trace for compiled/other languages
            try:
                from .visualizer_module import _safe_json
                from dotenv import load_dotenv
                load_dotenv()
                from langchain_groq import ChatGroq
                import os
                llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
                
                trace_prompt = f"""Simulate line-by-line execution of this {self.editor_language} code like a high-fidelity compiler/CPU.
Return a RAW JSON list of steps. 
YOU MUST SIMULATE ALL LOOP ITERATIONS truthfully. Do not skip steps.

EACH STEP MUST FOLLOW THIS SCHEMA:
{{"line": <line_number_int>, "locals": {{"var_name": "value"}}, "stdout": "last printed", "func_name": "function_active", "event": "line"}}
Instructions:
1. Map every variable change in 'locals'.
2. Show the loop entering, EACH iteration, and the exit.
3. If there are infinite loops, cap at 30 steps.

Max 30 steps. Return ONLY the JSON list. No talking.
Code:
{self.editor_code}"""
                trace_resp = await loop.run_in_executor(None, lambda: llm.invoke(trace_prompt).content)
                self.trace_steps = _safe_json(trace_resp, is_list=True)
            except Exception as e:
                self.trace_steps = [{"line": "1", "vars": "{}", "stdout": f"AI Trace Parse Error: {e}", "func_name": "main"}]
        self.is_running = False

    async def analyze_code(self):
        if self.is_running: return
        self.is_running = True
        self.is_ai_fixing = True
        self.ai_explanation = "🧠 Neural Intelligence is reviewing your code logic..."
        self.ai_fixed_code = ""
        yield
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, _analyze_code_sync, self.editor_code, self.editor_language)
        self.ai_explanation = res.get("explanation", "AI provided explanation.")
        self.ai_fixed_code = res.get("fixed_code", "")
        self.is_running = False

    def apply_ai_fix(self):
        if self.ai_fixed_code:
            self.editor_code = self.ai_fixed_code
            self.update_version += 1
            self.ai_fixed_code = ""
            self.ai_explanation = ""
            self.is_ai_fixing = False

    def close_ai_fix(self):
        self.is_ai_fixing = False
        self.ai_explanation = ""
        self.ai_fixed_code = ""


# ── Page UI ───────────────────────────────────────────────────────────────────
def editor_page():
    return rx.vstack(
        navbar(active_page="Editor"),
        rx.box(
            rx.hstack(
                # LEFT: Editor
                rx.vstack(
                    rx.hstack(
                        rx.icon("code", color="#6B73FF", size=18),
                        rx.heading("NEURAL IDE", size="4", color="var(--text-color)"),
                        rx.spacer(),
                        rx.select(EditorState.supported_languages, value=EditorState.editor_language, on_change=EditorState.set_editor_language, width="110px", size="1", variant="soft"),
                        rx.select(EditorState.supported_themes, value=EditorState.editor_theme, on_change=EditorState.set_editor_theme, width="90px", size="1", variant="soft"),
                        rx.button(rx.icon("play", size=14), "RUN", on_click=EditorState.run_code, color_scheme="grass", size="1", is_loading=EditorState.is_running),
                        rx.button(rx.icon("zap", size=14), "AI FIX", on_click=EditorState.analyze_code, color_scheme="violet", size="1"),
                        rx.button(rx.icon("message-square", size=14), "ASK AI", on_click=ChatState.toggle_chat, color_scheme="iris", size="1"),
                        width="100%", align="center", padding="8px 14px", background="var(--navbar-bg)", border_bottom="1px solid var(--border-color)",
                    ),
                    rx.box(
                        rx.cond(
                            EditorState.is_hydrated,
                            rx.box(
                                MonacoEditor.create(
                                    key=f"editor-{EditorState.update_version}",
                                    width="100%", 
                                    height="100%", 
                                    language=EditorState.editor_language, 
                                    default_value=EditorState.editor_code, 
                                    theme=EditorState.editor_theme, 
                                    on_change=EditorState.set_editor_code,
                                    options={
                                        "fontSize": 14, 
                                        "minimap": {"enabled": False}, 
                                        "automaticLayout": True,
                                        "suggestSelection": "first",
                                        "quickSuggestions": {"other": True, "comments": False, "strings": True},
                                        "wordBasedSuggestions": True,
                                        "parameterHints": {"enabled": True},
                                        "suggestOnTriggerCharacters": True,
                                        "snippetSuggestions": "inline",
                                        "acceptSuggestionOnEnter": "on",
                                    }
                                ),
                                width="100%", height="100%"
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.spinner(size="3"),
                                    rx.text("Connecting to Neural Engine...", font_size="14px", color="var(--iris-9)"),
                                    align="center", spacing="3"
                                ),
                                width="100%", height="100%", background="rgba(0,0,0,0.2)"
                            )
                        ),
                        width="100%", height="calc(100vh - 120px)",
                    ),
                    width="50%", height="100%", spacing="0", border_right="1px solid var(--border-color)",
                ),
                # RIGHT: Output
                rx.vstack(
                    rx.hstack(
                        rx.icon("cpu", color="#6B73FF", size=16),
                        rx.cond(
                            EditorState.is_visualizing,
                            rx.heading("NEURAL TUTOR", size="3", color="var(--text-color)"),
                            rx.heading("TERMINAL", size="3", color="var(--text-color)"),
                        ),
                        rx.spacer(),
                        rx.cond(
                            EditorState.is_visualizing, 
                            rx.button("✕ Close", on_click=EditorState.toggle_visualize, size="1", variant="ghost", color_scheme="red"),
                            rx.button(rx.icon("trash-2", size=12), "Clear", on_click=EditorState.clear_terminal, size="1", variant="ghost", color_scheme="gray")
                        ),
                        width="100%", align="center", padding="10px 14px", background="var(--navbar-bg)", border_bottom="1px solid var(--border-color)",
                    ),
                    rx.cond(
                        EditorState.is_visualizing,
                        rx.vstack(
                            rx.hstack(
                                rx.button(rx.icon("chevrons-left"), on_click=EditorState.prev_step, size="1"),
                                rx.cond(EditorState.is_playing, rx.button(rx.icon("pause"), on_click=EditorState.stop_playback, color_scheme="red", size="1"), rx.button(rx.icon("play"), on_click=EditorState.play_steps, color_scheme="green", size="1")),
                                rx.button(rx.icon("chevrons-right"), on_click=EditorState.next_step, size="1"),
                                width="100%", spacing="2", align="center", padding="8px 12px",
                            ),
                            rx.box(
                                rx.text(
                                    EditorState.current_step["vars"].to(str), 
                                    font_family="monospace", 
                                    font_size="11px"
                                ), 
                                padding="6px", 
                                background="var(--card-bg)"
                            ),
                            width="100%",
                        ),
                        rx.box(
                            rx.scroll_area(
                                rx.vstack(
                                    # Neural AI Fix Result
                                    rx.cond(
                                        EditorState.is_ai_fixing,
                                        rx.vstack(
                                            rx.hstack(
                                                rx.icon("sparkles", color="#6B73FF", size=16),
                                                rx.text("Neural Intelligence Fix", font_weight="bold", size="2"),
                                                rx.spacer(),
                                                rx.button(rx.icon("x"), on_click=EditorState.close_ai_fix, variant="ghost", size="1"),
                                                width="100%", align="center", padding_bottom="8px", border_bottom="1px solid var(--border-color)",
                                            ),
                                            rx.markdown(EditorState.ai_explanation, class_name="chat-markdown", component_map=markdown_components(EditorState.editor_language)),
                                            rx.cond(
                                                EditorState.ai_fixed_code != "",
                                                rx.vstack(
                                                    rx.box(
                                                        rx.code_block(
                                                            EditorState.ai_fixed_code, 
                                                            theme="vs-dark", 
                                                            language=EditorState.editor_language, 
                                                            custom_style={"backgroundColor": "transparent", "padding": "0"},
                                                            width="100%",
                                                        ),
                                                        rx.button(
                                                            rx.icon("copy", size=14),
                                                            on_click=rx.set_clipboard(EditorState.ai_fixed_code),
                                                            variant="solid", color_scheme="blue", size="1",
                                                            position="absolute", top="12px", right="12px", z_index="2000"
                                                        ),
                                                        class_name="neural-code-container",
                                                        padding="45px 15px 15px 15px",
                                                        height="60vh",
                                                        overflow_y="auto",
                                                        position="relative",
                                                        width="100%",
                                                    ),
                                                    rx.button(
                                                        rx.icon("check-check", size=14), "APPLY FIX",
                                                        on_click=EditorState.apply_ai_fix,
                                                        color_scheme="grass", size="2", class_name="glow-btn",
                                                        width="100%",
                                                        box_shadow="0 0 15px rgba(0, 200, 0, 0.3)",
                                                    ),
                                                    width="100%", spacing="2",
                                                ),
                                            ),
                                            width="100%", padding="16px", background="rgba(107,115,255,0.05)", border="1px solid rgba(107,115,255,0.2)", border_radius="10px", margin_bottom="20px",
                                        ),
                                    ),
                                    rx.foreach(EditorState.execution_logs, lambda log: rx.box(
                                        rx.vstack(
                                            rx.hstack(rx.badge(log.category, size="1"), rx.spacer(), rx.moment(log.timestamp, format="h:mm:ss A", font_size="10px", color="var(--gray-9)")),
                                            rx.text(log.content, font_family="monospace", font_size="12px", white_space="pre-wrap"),
                                            align="start", spacing="1"
                                        ),
                                        padding="10px", border_left="2px solid #6B73FF", margin_bottom="8px"
                                    )),
                                    width="100%",
                                ),
                                height="100%",
                            ),
                            flex="1", width="100%", padding="12px",
                            height="calc(100vh - 110px)",
                        )
                    ),
                    width="50%", height="100%", spacing="0", background="var(--navbar-bg)",
                ),
                width="100%", height="100%",
            ),
            # Chat
            rx.cond(
                ChatState.show_chat,
                rx.box(
                    rx.vstack(
                        rx.hstack(rx.text("AI Assistant", font_weight="bold"), rx.spacer(), rx.button(rx.icon("x"), on_click=ChatState.toggle_chat, variant="ghost")),
                        rx.scroll_area(
                            rx.vstack(
                                rx.foreach(
                                    ChatState.messages, 
                                    lambda m: rx.box(
                                        rx.markdown(
                                            m.content,
                                            component_map=markdown_components(EditorState.editor_language),
                                        ), 
                                        padding="10px", 
                                        margin_bottom="10px",                                         background="transparent",
                                         border_radius="10px",
                                         border=rx.color_mode_cond("1px solid rgba(0,0,0,0.05)", "1px solid rgba(255,255,255,0.05)"),
                                         width="100%", 
                                         max_width="100%",
                                         overflow_x="hidden",
                                         box_sizing="border-box",
                                     )
                                ),
                                width="100%",
                                max_width="100%",
                                spacing="2",
                            ), 
                            id="chat-scroll-area", 
                            flex="1", 
                            scrollbars="both",
                            
                        ),
                        rx.hstack(
                            rx.text_area(
                                value=ChatState.input_text, 
                                on_change=ChatState.set_input_text, 
                                on_key_down=ChatState.handle_chat_keydown, 
                                flex="1", 
                                placeholder="Ask Neural Assistant...",
                                height="80px",
                                resize="none",
                                border_radius="10px",
                                id="chat-input-area",
                            ), 
                            rx.button(
                                rx.icon("send"), 
                                on_click=ChatState.send_message, 
                                is_loading=ChatState.is_loading, 
                                color_scheme="blue",
                                height="80px"
                            ),
                            width="100%",
                            spacing="2",
                            align="end",
                        ),
                        height="100%", width="100%", padding="15px",
                    ),
                    position="fixed", bottom="30px", right="30px", width="600px", height="85vh", background="var(--navbar-bg)", border="1px solid var(--border-color)", border_radius="15px", z_index="1000",
                    overflow="hidden", # Force containment
                    box_shadow="0 10px 40px rgba(0,0,0,0.5)",
                )
            ),
            width="100%", height="calc(100vh - 120px)",
        ),
        footer(),
        width="100%", height="100vh", spacing="0", overflow="hidden",
    )

def cfg_layout():
    return rx.vstack(
        navbar(active_page="CFG"),
        rx.box(
            rx.vstack(
                # TOP: Editor mini
                rx.vstack(
                    rx.hstack(
                        rx.icon("code", size=18, color="#6B73FF"),
                        rx.text("Source Context", font_weight="bold", size="3"),
                        rx.spacer(),
                        rx.select(
                            EditorState.supported_languages,
                            value=EditorState.editor_language,
                            on_change=EditorState.set_editor_language,
                            size="1",
                            variant="surface",
                            color_scheme="blue",
                            width="110px",
                        ),
                        rx.button(
                            rx.icon("refresh-cw", size=14),
                            on_click=EditorState.generate_cfg_only,
                            size="1",
                            variant="soft",
                            color_scheme="iris",
                            is_loading=EditorState.is_running
                        ),
                        width="100%", align="center", padding_x="12px", spacing="2",
                    ),
                    rx.box(
                        rx.cond(
                            EditorState.is_hydrated,
                            rx.box(
                                MonacoEditor.create(
                                    id="cfg-editor-view",
                                    value=EditorState.editor_code,
                                    language=EditorState.editor_language,
                                    theme="vs-dark",
                                    options={"readOnly": True, "minimap": {"enabled": False}, "fontSize": 12},
                                    width="100%",
                                    height="100%",
                                ),
                                width="100%", height="100%"
                            )
                        ),
                        flex="1", width="100%", border="1px solid var(--border-color)", border_radius="10px", overflow="hidden"
                    ),
                    width="100%", height="35vh", spacing="3"
                ),
                # BOTTOM: CFG Visualization
                rx.vstack(
                    rx.hstack(
                        rx.icon("git-branch", size=18, color="#9747FF"),
                        rx.text("Neural Flow Graph (CFG)", font_weight="bold", size="3"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("refresh-cw", size=14), "Regenerate CFG",
                            on_click=EditorState.generate_cfg_only,
                            size="1", color_scheme="iris", variant="soft",
                            is_loading=EditorState.is_running
                        ),
                        width="100%", align="center", padding_x="12px"
                    ),
                    rx.box(
                        rx.html(EditorState.cfg_html, height="60vh", width="100%"),
                        width="100%", height="60vh",
                        background="var(--bg-color)", overflow="hidden",
                        border="1px solid var(--border-color)", border_radius="10px"
                    ),
                    flex="1", width="100%", spacing="3"
                ),
                width="100%", spacing="6", padding="20px"
            ),
            width="100%", height="calc(100vh - 120px)", background="var(--bg-color)"
        ),
        footer(),
        width="100%", height="100vh", spacing="0"
    )

def cfg_page(): 
    return cfg_layout()
