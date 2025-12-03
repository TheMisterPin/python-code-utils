# Generator Helpers

These helpers work on the artifacts produced by the extractor scripts and help you keep documentation in sync with the running services.

## list-unused-endpoints.py

**Features**
- Crawls `Controller.cs` files and reports every `[HttpPost]` endpoint, including inferred `Route` attributes and `AllowAnonymous` decorations.
- Optionally cross-references the Markdown output from `extract-endpoints.py` to split controllers into Referenced and Unreferenced lists.
- Emits either `post_endpoints.md` (with every POST route) or a combined report that lists which endpoints are still referenced by the frontend.

**How to Run**
1. `python documents/generators/list-unused-endpoints.py ./server --output reports/post_endpoints.md`
2. Add `--references docs/api_references.md` to mark endpoints that are referenced from the TypeScript side.

**Usage Example**
```
$ python documents/generators/list-unused-endpoints.py ./server --references docs/api_references.md --output docs/post_endpoints.md
Found 52 controller files to scan.
Wrote 32 unique POST endpoints to docs/post_endpoints.md.
```

## make-md-files.py

**Features**
- Walks the provided `src` tree (default `src`) and records every `.ts` file that should have generated Markdown documentation.
- Skips files that match excluded patterns (like `routing.module.ts` or `.module.ts`).
- Writes or updates `docs/autodocs/not-documented.md` with a bullet list of files that still need manual touches.

**How to Run**
1. `python documents/generators/make-md-files.py`
2. Use `--dest docs/autodocs/generated` to point to the directory that will host the generated Markdown.

**Usage Example**
```
$ python documents/generators/make-md-files.py path/to/frontend --dest docs/autodocs/generated
Scanning path/to/frontend …
Generating not-documented.md …
Added to list: path/to/frontend/app/app.component.ts
Done.
```

## write-docs.py

**Features**
- Reads `docs/autodocs/not-documented.md`, opens or creates matching Markdown files under `docs/autodocs/generated`, and replaces placeholder content with higher-level documentation that describes purpose, flows, and interactions.
- Sends prompts to the LLM hosted at `OLLAMA_URL` (default `http://127.0.0.1:11434/api/generate`) so the response can stay in Italian with a fixed metadata block.
- Moves successfully documented entries from `not-documented.md` to `docs/autodocs/documented.md` and supports multiple iterations to bite through a long backlog.

**How to Run**
1. Ensure Ollama is running with a model matching `MODEL_NAME` (default `deepseek-v3.1:671b-cloud`).
2. Install `requests` or rely on the standard library HTTP client.
3. Run `python documents/generators/write-docs.py --iterations 3` to process up to three passes over the backlog.

**Usage Example**
```
$ python documents/generators/write-docs.py
[INFO] Genero documentazione per docs/autodocs/generated/app.component.md
[INFO] Documentazione completata per docs/autodocs/generated/app.component.md
--- Iterazione 1/1 ---
Totale file completati: 1.
```
