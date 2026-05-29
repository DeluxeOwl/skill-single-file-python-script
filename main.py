#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "fastapi",
#     "uvicorn",
# ]
# ///

import uvicorn

import click

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI()

HTML = """\
<!--
Everything lives in this one HTML file. No bundler, no node_modules, no build step.

STACK (all loaded via CDN):
- React 19 + ReactDOM (ESM via esm.sh)
- Tailwind CSS v4 (browser runtime)
- shadcn components via "shadcn-ui-bundled/standalone"
- Babel standalone (so you can write TSX directly in a <script> tag)

HOW IT WORKS:
1. Tailwind v4 browser runtime is loaded and configured in <style type="text/tailwindcss">.
2. The @theme inline block maps Tailwind color utilities (bg-primary, text-muted-foreground, etc.)
    to CSS custom properties (--primary, --muted-foreground, etc.) defined in :root.
    This block is REQUIRED — without it, shadcn component styles won't render.
3. The import map lets you use bare specifiers: import { Button } from "shadcn"
4. Babel compiles <script type="text/babel"> blocks so you can write TSX inline.
5. Your app code goes in the final <script> tag — import React hooks, shadcn components,
    and render into #root. That's it.

Available shadcn (baseui variant) components (import from "shadcn"):
  Accordion, Alert, AlertDialog, AspectRatio, Avatar, Badge, Breadcrumb,
  Button, Calendar, Card, Carousel, Chart, Checkbox, Collapsible, Combobox,
  Command, ContextMenu, Dialog, Drawer, DropdownMenu, Empty, Field,
  HoverCard, Input, InputGroup, InputOTP, Item, Kbd, Label, Menubar,
  NativeSelect, NavigationMenu, Pagination, Popover, Progress, RadioGroup,
  Resizable, ScrollArea, Select, Separator, Sheet, Sidebar, Skeleton,
  Slider, Spinner, Switch, Table, Tabs, Textarea, Toggle, ToggleGroup,
  Tooltip, Toaster
  (Each component family has sub-components, e.g. Card → CardHeader, CardTitle, CardContent, etc.)

CUSTOMIZATION:
- To change the theme, edit the CSS custom properties in :root (uses oklch colors).
- To add dark mode, add a .dark {} block overriding the same variables.
- To install extra npm packages, add them to the import map pointing to esm.sh.

RULES:
- Keep everything in this single file.
- Write your React TSX inside <script type="text/babel" data-type="module" data-presets="tsx-auto">.
- Use Tailwind classes for all styling.
- Import shadcn components as needed from "shadcn".
-->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My application</title>

  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>

  <!-- Minimal theme: maps Tailwind classes (bg-primary, etc.) to CSS vars -->
  <style type="text/tailwindcss">
    @theme inline {
      --font-sans: ui-sans-serif, system-ui, sans-serif;
      --color-background: var(--background);
      --color-foreground: var(--foreground);
      --color-primary: var(--primary);
      --color-primary-foreground: var(--primary-foreground);
      --color-secondary: var(--secondary);
      --color-secondary-foreground: var(--secondary-foreground);
      --color-muted: var(--muted);
      --color-muted-foreground: var(--muted-foreground);
      --color-accent: var(--accent);
      --color-accent-foreground: var(--accent-foreground);
      --color-destructive: var(--destructive);
      --color-card: var(--card);
      --color-card-foreground: var(--card-foreground);
      --color-border: var(--border);
      --color-input: var(--input);
      --color-ring: var(--ring);
      --radius-sm: calc(var(--radius) * 0.6);
      --radius-md: calc(var(--radius) * 0.8);
      --radius-lg: var(--radius);
      --radius-xl: calc(var(--radius) * 1.4);
      --radius-2xl: calc(var(--radius) * 1.8);
    }
    :root {
      --background: oklch(0.99 0 0);
      --foreground: oklch(0.15 0 0);
      --primary: oklch(0.205 0 0);
      --primary-foreground: oklch(0.985 0 0);
      --secondary: oklch(0.96 0 0);
      --secondary-foreground: oklch(0.205 0 0);
      --muted: oklch(0.96 0 0);
      --muted-foreground: oklch(0.556 0 0);
      --accent: oklch(0.96 0 0);
      --accent-foreground: oklch(0.205 0 0);
      --destructive: oklch(0.577 0.245 27.325);
      --card: oklch(1 0 0);
      --card-foreground: oklch(0.15 0 0);
      --border: oklch(0.922 0 0);
      --input: oklch(0.922 0 0);
      --ring: oklch(0.708 0 0);
      --radius: 0.625rem;
    }
    @layer base {
      * { @apply border-border; }
      body { @apply bg-background text-foreground; }
    }
  </style>

  <script type="importmap">
  {
    "imports": {
      "react": "https://esm.sh/react@19",
      "react/jsx-runtime": "https://esm.sh/react@19/jsx-runtime",
      "react/jsx-dev-runtime": "https://esm.sh/react@19/jsx-dev-runtime",
      "react-dom": "https://esm.sh/react-dom@19",
      "react-dom/client": "https://esm.sh/react-dom@19/client",
      "shadcn": "https://esm.sh/shadcn-ui-bundled/standalone"
    }
  }
  </script>

  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script>
    Babel.registerPreset("tsx-auto", {
      presets: [
        [Babel.availablePresets["react"], { runtime: "automatic" }],
        [Babel.availablePresets["typescript"], { isTSX: true, allExtensions: true }],
      ],
    });
  </script>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel" data-type="module" data-presets="tsx-auto">
    import { useState } from "react";
    import { createRoot } from "react-dom/client";
    import { Button, Card, CardHeader, CardTitle, CardContent } from "shadcn";

    function App() {
      const [count, setCount] = useState(0);

      return (
        <div className="min-h-screen flex items-center justify-center">
          <Card className="w-80">
            <CardHeader>
              <CardTitle>Counter</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <span className="text-4xl font-bold">{count}</span>
              <Button onClick={() => setCount(count + 1)}>Increment</Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    createRoot(document.getElementById("root")!).render(<App />);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@click.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind host")
@click.option("--port", default=8765, type=int, help="Bind port")
def main(host: str, port: int | None):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
