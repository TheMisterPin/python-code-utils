"""Utility per completare la documentazione generata automaticamente."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional
import argparse

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "deepseek-v3.1:671b-cloud"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_placeholder(content: str) -> bool:
	"""Verifica se il markdown contiene ancora il testo generato automaticamente."""

	lines = content.strip().splitlines()
	if len(lines) != 6:
		return False

	first, _, source_line, _, separator, tail = lines
	if not first.startswith("# "):
		return False
	if not source_line.strip().startswith("Source: `"):
		return False
	if not source_line.strip().endswith("`"):
		return False
	if separator.strip() != "---":
		return False
	return tail.strip() == "Content can be added here."


def extract_source_path(content: str) -> Optional[Path]:
	"""Ricava il path del file sorgente dal blocco "Source"."""

	for line in content.splitlines():
		stripped = line.strip()
		if stripped.startswith(" " in stripped[9:]:
			start = stripped.find("`")
			end = stripped.rfind("`")
			if start != -1 and end != -1 and end > start:
				return Path(stripped[start + 1 : end])
	return None


def call_ollama(prompt: str) -> str:
	"""Invia il prompt a Ollama e restituisce la risposta testuale."""

	payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}

	print("[INFO] Invio richiesta a Ollama…")
	try:
		import requests  # type: ignore

		response = requests.post(OLLAMA_URL, json=payload, timeout=None)
		print("[INFO] Ollama is processing the request...")
		response.raise_for_status()
		data = response.json()
	except ImportError:
		from urllib.request import Request, urlopen

		request = Request(
			OLLAMA_URL,
			data=json.dumps(payload).encode("utf-8"),
			headers={"Content-Type": "application/json"},
		)
		print("[INFO] Ollama is processing the request...")
		with urlopen(request, timeout=None) as result:
			data = json.loads(result.read().decode("utf-8"))
	except Exception as exc:  # pragma: no cover
		raise RuntimeError(f"Errore chiamando Ollama: {exc}") from exc

	if "response" not in data:
		raise RuntimeError("Risposta inesperata da Ollama: manca 'response'")

	print("[INFO] Risposta ricevuta da Ollama.")
	return str(data["response"]).strip()


def build_prompt(source_code: str, source_path: Path, display_path: str) -> str:
	"""Costruisce il prompt per ottenere spiegazioni in italiano."""

	return (
		"Sei un assistente tecnico che redige documentazione in italiano per un pubblico non tecnico.\n"
		"Produci un testo chiaro, ordinato e senza gergo complesso, descrivendo scopo generale, flussi principali e comportamenti rilevanti.\n"
		"La risposta deve iniziare SEMPRE con il blocco metadata seguente, sostituendo solo i valori tra parentesi angolari e mantenendo il campo Path come indicato. Non aggiungere altri caratteri o titoli prima del blocco.\n"
		f"---\nProgetto: WSpace\nArgomento: <descrivi il tema principale>\nFunzionalita: <descrivi la funzionalita chiave>\nTipo di File: <indica la tipologia>\nPath : {display_path}\n---\n"
		"Dopo il blocco metadata, continua con sezioni Markdown (esempi: Introduzione, Come funziona, Interazioni importanti, Gestione errori, Suggerimenti d'uso) scritte in modo comprensibile.\n"
		"Non inserire blocchi di codice, non usare backtick e non produrre sequenze come ```yaml.\n"
		"Concludi con una sintesi che spieghi l'utilita pratica per l'utente finale.\n\n"
		f"File: {source_path.name}\n"
		"Contenuto sorgente:\n"
		"```typescript\n"
		f"{source_code}\n"
		"```"
	)


def update_markdown(md_path: Path, documentation: str) -> None:
	"""Aggiunge la documentazione generata in coda al file markdown."""

	original = md_path.read_text(encoding="utf-8")
	new_content = original.rstrip() + "\n\n" + documentation.strip() + "\n"
	md_path.write_text(new_content, encoding="utf-8")


def process_markdown(md_path: Path) -> bool:
	"""Analizza e aggiorna un singolo file markdown."""

	content = md_path.read_text(encoding="utf-8")
	if not is_placeholder(content):
		return False

	source_path = extract_source_path(content)
	if source_path is None or not source_path.exists():
		print(f"[WARN] Path sorgente mancante per {md_path}")
		return False

	print(f"[INFO] Genero documentazione per {md_path}")
	source_code = source_path.read_text(encoding="utf-8")
	print("[INFO] Costruzione del prompt…")
	try:
		relative_path = source_path.relative_to(PROJECT_ROOT)
		display_path = "\\" + relative_path.as_posix().replace("/", "\\")
	except ValueError:
		display_path = str(source_path)
	prompt = build_prompt(source_code, source_path, display_path)
	print("[INFO] Richiesta documentazione al modello…")
	documentation = call_ollama(prompt)
	print("[INFO] Scrittura della documentazione nel file markdown…")
	update_markdown(md_path, documentation)
	print(f"[OK] Aggiornato {md_path}")
	return True


def read_not_documented(file_path: Path) -> list[tuple[str, Path]]:
    """Legge la lista dei file non documentati."""
    if not file_path.exists():
        return []
    lines = file_path.read_text(encoding="utf-8").splitlines()
    result = []
    for line in lines:
        if line.startswith("- "):
            parts = line[2:].split(": ", 1)
            if len(parts) == 2:
                name, path_str = parts
                result.append((name, Path(path_str)))
    return result


def remove_from_list(file_path: Path, name: str, ts_path: Path):
    """Rimuove un elemento dalla lista."""
    if not file_path.exists():
        return
    lines = file_path.read_text(encoding="utf-8").splitlines()
    new_lines = [line for line in lines if not (line.startswith("- ") and f"{name}: {ts_path}" in line)]
    file_path.write_text("\n".join(new_lines), encoding="utf-8")


def add_to_list(file_path: Path, name: str, ts_path: Path):
    """Aggiunge un elemento alla lista."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write("# File documentati\n\n")
    content = file_path.read_text(encoding="utf-8")
    if f"{name}: {ts_path}" not in content:
        with file_path.open("a", encoding="utf-8") as f:
            f.write(f"- {name}: {ts_path}\n")


def run_once(base_dir: Path, docs_root: Path) -> int:
    processed = 0
    not_documented_file = base_dir / "docs" / "autodocs" / "not-documented.md"
    documented_file = base_dir / "docs" / "autodocs" / "documented.md"
    items = read_not_documented(not_documented_file)
    for name, ts_path in items:
        relative_path = ts_path.relative_to(base_dir / "src")
        md_path = docs_root / relative_path.with_suffix(".md")
        # Create if not exists
        if not md_path.exists():
            md_path.parent.mkdir(parents=True, exist_ok=True)
            with md_path.open("w", encoding="utf-8") as f:
                f.write(f"# {name}\n\n")
                f.write(f"  \n")
                f.write("\n---\n")
                f.write("Content can be added here.\n")
        try:
            if process_markdown(md_path):
                processed += 1
                # Remove from not-documented
                remove_from_list(not_documented_file, name, ts_path)
                # Add to documented
                add_to_list(documented_file, name, ts_path)
        except Exception as exc:
            print(f"[ERROR] {md_path}: {exc}")
    print(f"Completati {processed} file.")
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Completa la documentazione generata automaticamente."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Numero di cicli di scansione dei markdown (default 1).",
    )
    args = parser.parse_args()

    if args.iterations < 1:
        print("Il numero di iterazioni deve essere almeno 1.")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parents[2]
    docs_root = base_dir / "docs" / "autodocs" / "generated"

    if not docs_root.is_dir():
        docs_root.mkdir(parents=True, exist_ok=True)

    total = 0
    for index in range(1, args.iterations + 1):
        print(f"--- Iterazione {index}/{args.iterations} ---")
        total += run_once(base_dir, docs_root)

    print(f"Totale file completati: {total}.")


if __name__ == "__main__":
    main()