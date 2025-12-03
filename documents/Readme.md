# Document Utilities

This folder groups the tools that read code or API definitions and turn them into Markdown documentation. The subfolders split the workload into two stages:

- `documents/extractors` houses language-specific parsers that crawl through Python, TypeScript/JavaScript, and C# sources, extract docstrings/comments, and emit Markdown files (often under `./extracted`). Read [documents/extractors/Readme.md](documents/extractors/Readme.md) for the exact commands.
- `documents/generators` automates the final touches: listing unused endpoints, scaffolding `docs/autodocs/generated`, and even asking an LLM to fill placeholder sections with richer prose. See [documents/generators/Readme.md](documents/generators/Readme.md) for the generator checklist.

Use the extractor of your choice first to capture the raw documentation, then feed its output into the generator scripts whenever you want structured reports or AI-assisted write-ups.
