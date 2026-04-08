import reflex as rx
from .fingerprint import fingerprint_logic

CURSOR_JS = """
(function() {
  if (document.getElementById('__cursor_follower')) return;
  var f = document.createElement('div'); f.id='__cursor_follower'; f.className='cursor-follower';
  var d = document.createElement('div'); d.id='__cursor_dot'; d.className='cursor-dot';
  document.body.appendChild(f); document.body.appendChild(d);
  var mx = window.innerWidth/2, my = window.innerHeight/2, fx=mx, fy=my;
  document.addEventListener('mousemove',function(e){mx=e.clientX;my=e.clientY;d.style.transform='translate('+(mx-4)+'px,'+(my-4)+'px)';});
  function loop(){fx+=(mx-fx)*0.12;fy+=(my-fy)*0.12;f.style.transform='translate('+(fx-20)+'px,'+(fy-20)+'px)';requestAnimationFrame(loop);}
  loop();
  var sel='a,button,[role="button"],input,textarea,label';
  document.addEventListener('mouseover',function(e){if(e.target.matches&&(e.target.matches(sel)||e.target.closest(sel)))f.classList.add('cursor-hover');});
  document.addEventListener('mouseout',function(e){if(e.target.matches&&(e.target.matches(sel)||e.target.closest(sel)))f.classList.remove('cursor-hover');});
  document.addEventListener('mousedown',function(){f.classList.add('cursor-click');});
  document.addEventListener('mouseup',function(){f.classList.remove('cursor-click');});
})();
"""

INTELLISENSE_JS = r"""
(function() {
    if (window.__intellisense_registered) return;
    window.__intellisense_registered = true;
    const check = setInterval(() => {
        if (typeof monaco === 'undefined') return;
        clearInterval(check);
        const suggestions = {
            python: [
                {label:'print',kind:monaco.languages.CompletionItemKind.Function,insertText:'print(${1:msg})',insertTextRules:4,detail:'Print to console'},
                {label:'input',kind:monaco.languages.CompletionItemKind.Function,insertText:'input("${1:prompt}")',insertTextRules:4,detail:'Read user input'},
                {label:'len',kind:monaco.languages.CompletionItemKind.Function,insertText:'len(${1:obj})',insertTextRules:4,detail:'Get length of object'},
                {label:'range',kind:monaco.languages.CompletionItemKind.Function,insertText:'range(${1:n})',insertTextRules:4,detail:'Generate range of numbers'},
                {label:'if',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'if ${1:condition}:\n    ${2:pass}',insertTextRules:4},
                {label:'elif',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'elif ${1:condition}:\n    ${2:pass}',insertTextRules:4},
                {label:'else',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'else:\n    ${1:pass}',insertTextRules:4},
                {label:'for',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'for ${1:i} in ${2:iterable}:\n    ${3:pass}',insertTextRules:4},
                {label:'while',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'while ${1:condition}:\n    ${2:pass}',insertTextRules:4},
                {label:'def',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'def ${1:name}(${2:args}):\n    ${3:pass}',insertTextRules:4},
                {label:'import',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'import ${1:module}',insertTextRules:4},
                {label:'from',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'from ${1:module} import ${2:name}',insertTextRules:4},
                {label:'class',kind:monaco.languages.CompletionItemKind.Snippet,insertText:'class ${1:Name}:\n    def __init__(self):\n        ${2:pass}',insertTextRules:4},
                {label:'try',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'try:\n    ${1:pass}\nexcept Exception as e:\n    ${2:print(e)}',insertTextRules:4},
            ],
            javascript: [
                {label:'console.log',kind:monaco.languages.CompletionItemKind.Function,insertText:'console.log(${1:msg})',insertTextRules:4},
                {label:'if',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'if (${1:condition}) {\n    ${2}\n}',insertTextRules:4},
                {label:'let',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'let ${1:name} = ${2:value};',insertTextRules:4},
                {label:'const',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'const ${1:name} = ${2:value};',insertTextRules:4},
                {label:'function',kind:monaco.languages.CompletionItemKind.Snippet,insertText:'function ${1:name}(${2:args}) {\n    ${3}\n}',insertTextRules:4},
                {label:'arrow',kind:monaco.languages.CompletionItemKind.Snippet,insertText:'const ${1:fn} = (${2:args}) => {\n    ${3}\n};',insertTextRules:4},
                {label:'import',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'import ${1:name} from "${2:module}";',insertTextRules:4},
            ],
            java: [
                {label:'System.out.println',kind:monaco.languages.CompletionItemKind.Function,insertText:'System.out.println(${1:msg});',insertTextRules:4},
                {label:'public static void main',kind:monaco.languages.CompletionItemKind.Snippet,insertText:'public static void main(String[] args) {\n    ${1}\n}',insertTextRules:4},
                {label:'if',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'if (${1:condition}) {\n    ${2}\n}',insertTextRules:4},
                {label:'int',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'int ${1:name} = ${2:0};',insertTextRules:4},
            ],
            cpp: [
                {label:'std::cout',kind:monaco.languages.CompletionItemKind.Variable,insertText:'std::cout << ${1:value} << std::endl;',insertTextRules:4},
                {label:'vector',kind:monaco.languages.CompletionItemKind.Class,insertText:'std::vector<${1:type}> ${2:name};',insertTextRules:4},
                {label:'if',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'if (${1:condition}) {\n    ${2}\n}',insertTextRules:4},
                {label:'int main',kind:monaco.languages.CompletionItemKind.Snippet,insertText:'int main() {\n    ${1}\n    return 0;\n}',insertTextRules:4},
            ],
            c: [
                {label:'printf',kind:monaco.languages.CompletionItemKind.Function,insertText:'printf("${1:%s}\\n", ${2:var});',insertTextRules:4},
                {label:'scanf',kind:monaco.languages.CompletionItemKind.Function,insertText:'scanf("${1:%d}", &${2:var});',insertTextRules:4},
                {label:'if',kind:monaco.languages.CompletionItemKind.Keyword,insertText:'if (${1:condition}) {\n    ${2}\n}',insertTextRules:4},
            ]
        };
        Object.keys(suggestions).forEach(lang => {
            monaco.languages.registerCompletionItemProvider(lang, {
                provideCompletionItems(model, pos) {
                    const w = model.getWordUntilPosition(pos);
                    const range = {startLineNumber:pos.lineNumber,endLineNumber:pos.lineNumber,startColumn:w.startColumn,endColumn:w.endColumn};
                    return {suggestions: suggestions[lang].map(s=>({...s,range}))};
                }
            });
        });
    }, 500);
})();
"""

def navbar(active_page: str = None):
    def nav_link(text, href):
        is_active = active_page == text
        return rx.link(
            text,
            href=href,
            class_name=f"nav-link {'nav-link-active' if is_active else ''}"
        )

    return rx.fragment(
        rx.script(CURSOR_JS),
        rx.script(INTELLISENSE_JS),
        fingerprint_logic(),
        rx.hstack(
            rx.hstack(
                rx.image(src="/logo.png", width="32px", height="auto", border_radius="4px"),
                rx.text("Neural Compile (AI-Driven Code Reviewer)",
                    font_weight="800",
                    font_size="20px",
                    background="linear-gradient(90deg, #6B73FF, #9747FF)",
                    background_clip="text",
                    color="transparent",
                    letter_spacing="-0.5px",
                ),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                nav_link("Home", "/"),
                nav_link("Analyzer", "/analyze"),
                nav_link("Editor", "/editor"),
                nav_link("CFG", "/cfg"),
                nav_link("AST", "/ast"),
                nav_link("Visualize", "/visualizer"),
                nav_link("History", "/history"),
                nav_link("Contact", "/contact"),
                nav_link("About", "/about"),
                rx.button(
                    rx.color_mode_cond(
                        light=rx.icon("moon", size=16),
                        dark=rx.icon("sun", size=16),
                    ),
                    on_click=rx.toggle_color_mode,
                    variant="ghost", size="2",
                ),
                spacing="5", align="center",
            ),
            class_name="navbar-glass",
            padding="14px 32px",
            width="100%",
            position="sticky",
            top="0",
            z_index="100",
        ),
    )
 
 
def footer():
    return rx.center(
        rx.vstack(
            rx.text(
                "© Neural Compile 2026. All Rights Reserved",
                font_size="12px",
                color="gray",
                font_weight="500",
                letter_spacing="0.5px",
            ),
            rx.hstack(
                rx.text("Neural Network & NLP Analysis Engine", font_size="10px", color="var(--iris-8)"),
                spacing="4",
                align="center",
            ),
            align="center",
            spacing="1",
            padding_y="40px",
            width="100%",
            opacity="0.8",
        ),
        width="100%",
    )
