"""Conversational, tool-using table-QA agent on the OpenAI Agents SDK.

The agent reads a table, REASONS about the question, and calls a real
`calculator` function tool (native function calling, not a text protocol) when
the answer requires computation. It must answer from the table only, and emits
INSUFFICIENT when the table does not contain the answer (the abstention metric).

Provider-agnostic: runs on OpenAI, or any OpenAI-compatible endpoint (Groq) via
LLM_PROVIDER. Tracing upload is disabled; we capture the tool-call trajectory
locally from the run result so the evaluation record stays self-contained and
no table content leaves the run.
"""
import ast
import asyncio
import contextlib
import contextvars
import io
import operator
import os
import time

from agents import (Agent, Runner, function_tool, set_tracing_disabled,
                    set_default_openai_client, OpenAIChatCompletionsModel)

import agent as base   # provider resolution + .env loading, reused

set_tracing_disabled(True)      # no trace upload; we record trajectories locally

# ---------------- the tool ----------------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv, ast.USub: operator.neg,
        ast.UAdd: operator.pos}


def _ev(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_ev(node.left), _ev(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_ev(node.operand))
    raise ValueError("unsupported expression")


@function_tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression and return the numeric result.

    Use this for ANY arithmetic: sums, differences, ratios, percentages.
    Example: expression="11/76*100" returns "14.473684210526317".
    Only numbers and + - * / % ** ( ) are allowed.
    """
    try:
        return str(_ev(ast.parse(expression.strip(), mode="eval").body))
    except Exception as e:                       # noqa: BLE001
        return f"ERROR: {e}"


@function_tool
def sequence_length(text: str) -> str:
    """Return the number of characters in a sequence or string from the table.

    Use this whenever a question depends on how LONG a sequence is (e.g. a DNA
    primer), instead of counting characters yourself. Whitespace is ignored.
    Example: text="ACGTACGT" returns "8".
    """
    return str(len("".join(str(text).split())))


# ---------------- code-execution tool (the table as a DataFrame) ----------------
_CUR_DF = contextvars.ContextVar("cur_df", default=None)

_SAFE_BUILTINS = {k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
                  for k in ("len", "sum", "min", "max", "abs", "round", "sorted", "list",
                            "dict", "set", "str", "int", "float", "range", "enumerate",
                            "zip", "any", "all", "print", "bool", "tuple")}


@function_tool
def run_python(code: str) -> str:
    """Run Python over the table, which is preloaded as a pandas DataFrame `df`.

    Query the DataFrame instead of copying numbers out of the table. `df` and
    `pd` are available. Return value of the last expression (or anything printed)
    is returned to you.
    Example: code="df[df['Exon']=='Exon 2']['Forward'].str.len().iloc[0]"
    """
    df = _CUR_DF.get()
    if df is None:
        return "ERROR: no table loaded"
    import pandas as pd
    g = {"df": df, "pd": pd, "__builtins__": _SAFE_BUILTINS}
    buf = io.StringIO()
    try:
        try:
            compiled = compile(code.strip(), "<tool>", "eval")
            with contextlib.redirect_stdout(buf):
                val = eval(compiled, g)       # noqa: S307 - restricted builtins
            out = buf.getvalue() + ("" if val is None else repr(val))
        except SyntaxError:
            compiled = compile(code.strip(), "<tool>", "exec")
            with contextlib.redirect_stdout(buf):
                exec(compiled, g)             # noqa: S102 - restricted builtins
            out = buf.getvalue()
    except Exception as e:                    # noqa: BLE001
        return f"ERROR: {type(e).__name__}: {e}"
    out = out.strip()
    return out[:2000] if out else "(no output - make the last line an expression)"


CODE_INSTRUCTIONS = (
    "You answer questions about a table. The table is ALSO available to you as a "
    "pandas DataFrame named `df` via the run_python tool. ALWAYS use run_python to "
    "read values and to compute - never copy numbers out of the table yourself and "
    "never do arithmetic mentally, because transcription is where mistakes happen. "
    "Inspect with code (e.g. df.columns, df.head()) before computing if unsure. "
    "Reply with ONLY the final answer on the last line: a number with its unit, or "
    "the exact cell text. If the table does not contain the answer, reply exactly "
    "INSUFFICIENT."
)


INSTRUCTIONS = (
    "You answer questions using ONLY the table given in the user message. "
    "Think briefly. Whenever the answer needs arithmetic you MUST call the "
    "calculator tool, and whenever it depends on the length of a sequence or "
    "string you MUST call sequence_length. Never count or compute mentally. "
    "Reply with ONLY the final answer as the last line: a number with its unit, "
    "or the exact cell text. If the table does not contain the answer, reply "
    "exactly INSUFFICIENT."
)

_AGENTS = {}
_LOOP = None


def _loop():
    """One persistent loop for all calls: the cached AsyncOpenAI client is bound
    to the loop that created it, so asyncio.run() per call closes it mid-run."""
    global _LOOP
    if _LOOP is None or _LOOP.is_closed():
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
    return _LOOP


def _build_agent(toolset: str = "code"):
    """Create the Agent for a toolset, wiring the model for the active provider."""
    if toolset in _AGENTS:
        return _AGENTS[toolset]
    provider = base.resolve_provider()
    if provider == "groq":
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.environ["GROQ_API_KEY"],
                             base_url="https://api.groq.com/openai/v1")
        set_default_openai_client(client, use_for_tracing=False)
        model = OpenAIChatCompletionsModel(model=base.GROQ_MODEL, openai_client=client)
        model_id = base.GROQ_MODEL
    else:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        set_default_openai_client(client, use_for_tracing=False)
        model = OpenAIChatCompletionsModel(model=base.OPENAI_MODEL, openai_client=client)
        model_id = base.OPENAI_MODEL
    tools, instr = ([run_python], CODE_INSTRUCTIONS) if toolset == "code" \
        else ([calculator, sequence_length], INSTRUCTIONS)
    _AGENTS[toolset] = (Agent(name=f"TableQA-{toolset}", instructions=instr,
                              tools=tools, model=model), model_id, provider)
    return _AGENTS[toolset]


def _usage(result):
    u = getattr(getattr(result, "context_wrapper", None), "usage", None)
    return (getattr(u, "input_tokens", 0) or 0, getattr(u, "output_tokens", 0) or 0)


def _tool_calls(result) -> int:
    n = 0
    for it in getattr(result, "new_items", []) or []:
        if type(it).__name__ == "ToolCallItem":
            n += 1
    return n


def run_agent(question: str, table_csv: str, table_aware: bool = False,
              temperature: float = 0.0, toolset: str = "code") -> dict:
    """Answer one table question with the tool-using agent.

    toolset='code' -> run_python over a pandas DataFrame (recommended)
    toolset='calc' -> calculator + sequence_length (the transcription design)
    """
    from table_tools import csv_to_markdown, csv_to_dataframe
    table = csv_to_markdown(table_csv) if table_aware else table_csv.strip()
    if toolset == "code":
        try:
            _CUR_DF.set(csv_to_dataframe(table_csv))
        except Exception:
            _CUR_DF.set(None)
    agent_obj, model_id, provider = _build_agent(toolset)
    prompt = f"Table:\n{table}\n\nQuestion: {question}"
    last_err = None
    for attempt in range(3):
        try:
            result = _loop().run_until_complete(
                Runner.run(agent_obj, prompt, max_turns=8))
            last_err = None
            break
        except Exception as e:                  # noqa: BLE001
            last_err = e
            msg = str(e).lower()
            # malformed tool-call JSON isnot deterministic: retry the whole run.
            # Anything else (auth, quota) will not fix itself - fail fast.
            if "tool call" not in msg and "json" not in msg and "429" not in msg:
                break
            time.sleep(1.5 * (attempt + 1))
    if last_err is not None:
        return {"final": "", "error": str(last_err)[:200],
                "model": f"{provider}:{model_id}", "model_id": model_id,
                "prompt_tokens": 0, "completion_tokens": 0,
                "config": f"agent_{toolset}", "tool_calls": 0}
    text = str(getattr(result, "final_output", "") or "")
    pt, ct = _usage(result)
    return {"final": base._extract_final(text), "raw": text,
            "model": f"{provider}:{model_id}", "model_id": model_id,
            "prompt_tokens": pt, "completion_tokens": ct,
            "config": f"agent_{toolset}", "tool_calls": _tool_calls(result)}
