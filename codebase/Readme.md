# TypeScript Barrel File Generator

This script automatically creates and maintains `index.ts` barrel files throughout your TypeScript project, making imports cleaner and more maintainable.

## create-index.py

**Features**
- Recursively scans a target folder for TypeScript files (`.ts` and `.tsx`).
- Automatically generates or updates `index.ts` barrel files in every directory.
- Exports all TypeScript files and subfolders from each directory.
- Skips existing `index.ts` and `index.tsx` files to avoid circular references.
- Only updates files when changes are detected (smart diffing).
- Ignores hidden directories (those starting with `.`).

**What are Barrel Files?**  
Barrel files (`index.ts`) are re-export files that simplify imports by providing a single entry point for a directory. Instead of:
```typescript
import { UserService } from './services/user/UserService';
import { AuthService } from './services/auth/AuthService';
import { DataService } from './services/data/DataService';
```

You can write:
```typescript
import { UserService, AuthService, DataService } from './services';
```

**Output**  
All `index.ts` files are created **directly in your target project folder**, not in any separate output directory. The script modifies the project structure in place.

**How It Works**
1. Walks through every directory in the target folder.
2. For each directory:
   - Lists all subdirectories (excluding hidden ones starting with `.`)
   - Lists all `.ts` and `.tsx` files (excluding existing `index.ts`/`index.tsx`)
   - Generates export statements for subdirectories first, then files
   - Creates or updates the `index.ts` file with the exports
3. Only writes to disk if the content has changed.

**Generated Export Format**
```typescript
export * from "./subfolder1";
export * from "./subfolder2";
export * from "./ComponentA";
export * from "./ComponentB";
export * from "./utils";
```

**How to Run**

From anywhere in your system, run:
```bash
python create-index.py <target-folder>
```

Where `<target-folder>` is the root directory of your TypeScript project (or any subdirectory you want to process).

**Usage Examples**

Generate barrels for entire src directory:
```bash
$ python create-index.py C:\Projects\my-app\src
Scanning: C:\Projects\my-app\src

[UPDATED] C:\Projects\my-app\src\index.ts
[UPDATED] C:\Projects\my-app\src\components\index.ts
[SKIPPED] C:\Projects\my-app\src\utils\index.ts (no changes)
[UPDATED] C:\Projects\my-app\src\services\index.ts

Done! All index.ts files have been created/updated in: C:\Projects\my-app\src
```

Generate barrels for just the components folder:
```bash
$ python create-index.py C:\Projects\my-app\src\components
```

Re-run after adding new files:
```bash
$ python create-index.py C:\Projects\my-app\src
Scanning: C:\Projects\my-app\src

[UPDATED] C:\Projects\my-app\src\components\index.ts
[SKIPPED] C:\Projects\my-app\src\services\index.ts (no changes)

Done! All index.ts files have been created/updated in: C:\Projects\my-app\src
```

**When to Use This Script**
- Setting up a new TypeScript/React/Angular/Vue project with barrel exports
- Maintaining existing barrel files as your codebase grows
- Refactoring imports to use cleaner paths
- After adding new components, services, or utilities
- Before committing code to ensure all exports are up to date

**Best Practices**
- Run this script whenever you add new TypeScript files or folders
- Add it to your pre-commit hooks or CI/CD pipeline for automatic updates
- Review the generated `index.ts` files to ensure no unwanted exports
- Consider excluding test files by organizing them in separate directories

**Limitations**
- Does not analyze TypeScript code or handle circular dependencies
- Exports everything using `export *` (no selective exports)
- Does not handle default exports specially
- Skips directories starting with `.` (e.g., `.git`, `.vscode`)

**Error Handling**
The script validates:
- Target folder exists
- Target path is a directory
- Provides clear error messages if validation fails

**Integration with Build Tools**
You can add this to your `package.json` scripts:
```json
{
  "scripts": {
    "barrels": "python path/to/create-index.py ./src",
    "prebuild": "npm run barrels"
  }
}
```

This ensures barrel files are always up to date before building your project.
