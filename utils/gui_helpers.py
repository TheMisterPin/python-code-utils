#!/usr/bin/env python3
"""Shared Tkinter helpers for building simple GUI forms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


@dataclass
class FieldSpec:
    key: str
    label: str
    field_type: str
    default: Any = ""
    options: Optional[Iterable[str]] = None
    required: bool = False
    show: Optional[str] = None


def _add_browse_button(parent: tk.Widget, var: tk.StringVar, mode: str) -> tk.Button:
    def browse() -> None:
        if mode == "file":
            selection = filedialog.askopenfilename()
        elif mode == "save":
            selection = filedialog.asksaveasfilename()
        else:
            selection = filedialog.askdirectory()
        if selection:
            var.set(selection)

    button = ttk.Button(parent, text="Browse", command=browse)
    return button


def _create_field(
    parent: tk.Widget,
    field: FieldSpec,
) -> Tuple[tk.Variable, Optional[tk.Widget]]:
    if field.field_type == "bool":
        var: tk.Variable = tk.BooleanVar(value=bool(field.default))
        widget = ttk.Checkbutton(parent, variable=var)
    elif field.field_type == "choice":
        var = tk.StringVar(value=str(field.default))
        widget = ttk.Combobox(parent, textvariable=var, values=list(field.options or []), state="readonly")
    else:
        var = tk.StringVar(value=str(field.default) if field.default is not None else "")
        widget = ttk.Entry(parent, textvariable=var, show=field.show or "")

    return var, widget


def build_form(
    title: str,
    fields: List[FieldSpec],
    on_submit: Callable[[Dict[str, Any], Optional[tk.Text]], None],
    *,
    submit_label: str = "Run",
    include_output: bool = True,
    window_size: str = "700x500",
) -> None:
    root = tk.Tk()
    root.title(title)
    root.geometry(window_size)

    content = ttk.Frame(root, padding=12)
    content.pack(fill=tk.BOTH, expand=True)

    input_frame = ttk.Frame(content)
    input_frame.pack(fill=tk.X, expand=False)

    variables: Dict[str, tk.Variable] = {}
    row = 0
    for field in fields:
        label = ttk.Label(input_frame, text=field.label)
        label.grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))

        if field.field_type in {"file", "dir", "save"}:
            var = tk.StringVar(value=str(field.default) if field.default is not None else "")
            variables[field.key] = var
            entry = ttk.Entry(input_frame, textvariable=var)
            entry.grid(row=row, column=1, sticky=tk.EW, pady=4)
            button = _add_browse_button(input_frame, var, field.field_type)
            button.grid(row=row, column=2, sticky=tk.W, padx=(8, 0))
        else:
            var, widget = _create_field(input_frame, field)
            variables[field.key] = var
            if widget is not None:
                widget.grid(row=row, column=1, sticky=tk.EW, pady=4)

        input_frame.grid_columnconfigure(1, weight=1)
        row += 1

    output_text: Optional[tk.Text] = None
    if include_output:
        output_label = ttk.Label(content, text="Output")
        output_label.pack(anchor=tk.W, pady=(12, 4))
        output_frame = ttk.Frame(content)
        output_frame.pack(fill=tk.BOTH, expand=True)

        output_text = tk.Text(output_frame, height=12)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.configure(yscrollcommand=scrollbar.set)

    def handle_submit() -> None:
        values: Dict[str, Any] = {}
        for field in fields:
            value = variables[field.key].get()
            if field.field_type == "bool":
                values[field.key] = bool(value)
            else:
                values[field.key] = value

        missing = [field.label for field in fields if field.required and not values[field.key]]
        if missing:
            messagebox.showerror("Missing fields", f"Please fill: {', '.join(missing)}")
            return

        if output_text:
            output_text.delete("1.0", tk.END)

        on_submit(values, output_text)

    button = ttk.Button(content, text=submit_label, command=handle_submit)
    button.pack(pady=(12, 0), anchor=tk.E)

    root.mainloop()


def run_script_capture(script_path: str, args: List[str]) -> Tuple[int, str, str]:
    cmd = [sys.executable, script_path, "--cli", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    return result.returncode, stdout, stderr


def render_output(output_widget: Optional[tk.Text], stdout: str, stderr: str) -> None:
    if not output_widget:
        if stderr:
            messagebox.showerror("Error", stderr)
        elif stdout:
            messagebox.showinfo("Success", stdout)
        return

    if stdout:
        output_widget.insert(tk.END, stdout + "\n")
    if stderr:
        output_widget.insert(tk.END, "\n[stderr]\n" + stderr + "\n")
