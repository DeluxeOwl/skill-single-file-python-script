#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "fastapi",
#     "pydantic",
#     "uvicorn",
#     "pytest",
# ]
# ///

import sqlite3
import uvicorn
from abc import ABC, abstractmethod

import click

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# ── Domain ────────────────────────────────────────────────────────────

class Todo:
    def __init__(self, description: str) -> None:
        self.description = description
        self.done = False

    def toggle_done(self) -> None:
        self.done = not self.done


# ── Repository ────────────────────────────────────────────────────────

class TodoRepository(ABC):
    @abstractmethod
    def add(self, todo: Todo) -> None: ...

    @abstractmethod
    def list_all(self) -> list[Todo]: ...

    @abstractmethod
    def get_by_index(self, index: int) -> Todo: ...


class SqliteTodoRepository(TodoRepository):
    def __init__(self, db_path: str = "todos.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS todos ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  description TEXT NOT NULL,"
            "  done INTEGER NOT NULL DEFAULT 0"
            ")"
        )
        self._conn.commit()

    def add(self, todo: Todo) -> None:
        cur = self._conn.execute(
            "INSERT INTO todos (description, done) VALUES (?, ?)",
            (todo.description, int(todo.done)),
        )
        self._conn.commit()
        todo._rowid = cur.lastrowid  # track the row for toggle

    def list_all(self) -> list[Todo]:
        rows = self._conn.execute(
            "SELECT id, description, done FROM todos ORDER BY id"
        ).fetchall()
        todos: list[Todo] = []
        for rowid, description, done in rows:
            todo = Todo(description)
            todo.done = bool(done)
            todo._rowid = rowid
            todos.append(todo)
        return todos

    def get_by_index(self, index: int) -> Todo:
        row = self._conn.execute(
            "SELECT id, description, done FROM todos ORDER BY id LIMIT 1 OFFSET ?",
            (index,),
        ).fetchone()
        if row is None:
            raise IndexError(f"No todo at index {index}")
        rowid, description, done = row
        todo = Todo(description)
        todo.done = bool(done)
        todo._rowid = rowid
        return todo

    def save(self, todo: Todo) -> None:
        self._conn.execute(
            "UPDATE todos SET done = ? WHERE id = ?",
            (int(todo.done), todo._rowid),
        )
        self._conn.commit()


# ── Schemas ───────────────────────────────────────────────────────────

class AddTodoRequest(BaseModel):
    description: str

class TodoResponse(BaseModel):
    index: int
    description: str
    done: bool


# ── API ───────────────────────────────────────────────────────────────

api = APIRouter(prefix="/api")
repo = SqliteTodoRepository()


@api.post("/todos", response_model=TodoResponse, status_code=201)
async def add_todo(body: AddTodoRequest):
    todo = Todo(body.description)
    repo.add(todo)
    index = len(repo.list_all()) - 1
    return TodoResponse(index=index, description=todo.description, done=todo.done)


@api.get("/todos", response_model=list[TodoResponse])
async def list_todos():
    return [
        TodoResponse(index=i, description=t.description, done=t.done)
        for i, t in enumerate(repo.list_all())
    ]


@api.patch("/todos/{index}/toggle", response_model=TodoResponse)
async def toggle_todo_done(index: int):
    try:
        todo = repo.get_by_index(index)
    except IndexError:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.toggle_done()
    repo.save(todo)
    return TodoResponse(index=index, description=todo.description, done=todo.done)


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI()
app.include_router(api)

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
      "shadcn": "https://esm.sh/shadcn-ui-bundled/standalone",
      "@tanstack/react-query": "https://esm.sh/@tanstack/react-query@5?deps=react@19",
      "react-error-boundary": "https://esm.sh/react-error-boundary?deps=react@19",
      "ky": "https://esm.sh/ky",
      "react-hook-form": "https://esm.sh/react-hook-form?deps=react@19",
      "wouter": "https://esm.sh/wouter?deps=react@19"
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
    import { Suspense, useState, useEffect } from "react";
    import { createRoot } from "react-dom/client";
    import {
      QueryClient,
      QueryClientProvider,
      useSuspenseQuery,
      useMutation,
      useQueryClient,
    } from "@tanstack/react-query";
    import { ErrorBoundary } from "react-error-boundary";
    import ky, { HTTPError } from "ky";
    import { useForm } from "react-hook-form";
    import { Switch as RouteSwitch, Route, Link, useLocation } from "wouter";
    import {
      Button,
      Card, CardHeader, CardTitle, CardContent, CardDescription,
      Input,
      Checkbox,
      Separator,
      Spinner,
      Badge,
      Alert, AlertDescription,
    } from "shadcn";

    // ── Types ────────────────────────────────────────────────────

    interface Todo {
      index: number;
      description: string;
      done: boolean;
    }

    // ── Query keys ───────────────────────────────────────────────

    const todoKeys = {
      all: ["todos"] as const,
    } as const;

    // ── API client ──────────────────────────────────────────────

    const api = ky.create({ prefix: "/api" });

    const todoClient = {
      list: () => api.get("todos").json<Todo[]>(),
      add: (description: string) =>
        api.post("todos", { json: { description } }).json<Todo>(),
      toggleDone: (index: number) =>
        api.patch(`todos/${index}/toggle`).json<Todo>(),
    } as const;

    // ── Error handling ────────────────────────────────────────────

    function useErrorMessage(error: Error | null): string | null {
      const [message, setMessage] = useState<string | null>(null);

      useEffect(() => {
        if (!error) { setMessage(null); return; }

        if (error instanceof HTTPError) {
          error.response
            .json()
            .then((body: any) => setMessage(body?.detail ?? error.message))
            .catch(() => setMessage(error.message));
        } else {
          setMessage(error.message);
        }
      }, [error]);

      return message;
    }

    function AppErrorMessage({ error, retry }: { error: Error | null; retry?: () => void }) {
      const message = useErrorMessage(error);
      if (!message) return null;

      if (retry) {
        return (
          <Alert variant="destructive" className="my-4">
            <AlertDescription className="flex items-center justify-between">
              <span>{message}</span>
              <Button variant="outline" size="sm" onClick={retry}>Retry</Button>
            </AlertDescription>
          </Alert>
        );
      }

      return <p className="text-sm text-destructive">{message}</p>;
    }

    // ── Components ───────────────────────────────────────────────

    interface AddTodoFields {
      description: string;
    }

    function AddTodoForm() {
      const { register, handleSubmit, reset, formState: { isValid } } = useForm<AddTodoFields>({
        defaultValues: { description: "" },
      });
      const queryClient = useQueryClient();

      const mutation = useMutation({
        mutationFn: todoClient.add,
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: todoKeys.all });
          reset();
        },
      });

      const onSubmit = ({ description }: AddTodoFields) => {
        mutation.mutate(description.trim());
      };

      return (
        <div className="flex flex-col gap-2">
          <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
            <Input
              placeholder="What needs to be done?"
              {...register("description", { required: true, validate: (v) => v.trim().length > 0 })}
              disabled={mutation.isPending}
              className="flex-1"
            />
            <Button type="submit" disabled={mutation.isPending || !isValid}>
              {mutation.isPending ? "Adding…" : "Add"}
            </Button>
          </form>
          <AppErrorMessage error={mutation.error} />
        </div>
      );
    }

    function TodoItem({ todo }: { todo: Todo }) {
      const queryClient = useQueryClient();

      const mutation = useMutation({
        mutationFn: () => todoClient.toggleDone(todo.index),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: todoKeys.all });
        },
      });

      return (
        <div className="flex flex-col gap-1 py-2">
          <div className="flex items-center gap-3">
            <Checkbox
              checked={todo.done}
              disabled={mutation.isPending}
              onCheckedChange={() => mutation.mutate()}
            />
            <span className={todo.done ? "line-through text-muted-foreground" : ""}>
              {todo.description}
            </span>
          </div>
          <AppErrorMessage error={mutation.error} />
        </div>
      );
    }

    function TodoList({ filter }: { filter: "all" | "active" | "done" }) {
      const { data: todos } = useSuspenseQuery({
        queryKey: todoKeys.all,
        queryFn: todoClient.list,
      });

      const filtered = todos.filter((t) => {
        if (filter === "active") return !t.done;
        if (filter === "done") return t.done;
        return true;
      });

      if (filtered.length === 0) {
        const messages = {
          all: "No todos yet. Add one above!",
          active: "No active todos — everything is done!",
          done: "No completed todos yet.",
        } as const;
        return (
          <p className="text-sm text-muted-foreground text-center py-6">
            {messages[filter]}
          </p>
        );
      }

      return (
        <div className="divide-y">
          {filtered.map((todo) => (
            <TodoItem key={todo.index} todo={todo} />
          ))}
        </div>
      );
    }

    function ErrorFallback({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
      return <AppErrorMessage error={error} retry={resetErrorBoundary} />;
    }

    function LoadingFallback() {
      return (
        <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
          <Spinner className="h-4 w-4" />
          <span className="text-sm">Loading todos…</span>
        </div>
      );
    }

    // ── Pages ────────────────────────────────────────────────────

    function NavBar() {
      const [location] = useLocation();

      const links = [
        { href: "/", label: "All" },
        { href: "/active", label: "Active" },
        { href: "/done", label: "Done" },
      ] as const;

      return (
        <nav className="flex gap-2">
          {links.map(({ href, label }) => (
            <Link key={href} href={href}>
              <Badge
                variant={location === href ? "default" : "outline"}
                className="cursor-pointer"
              >
                {label}
              </Badge>
            </Link>
          ))}
        </nav>
      );
    }

    function TodoPage({ filter }: { filter: "all" | "active" | "done" }) {
      return (
        <div className="flex flex-col gap-4">
          <AddTodoForm />
          <Separator />
          <NavBar />
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <Suspense fallback={<LoadingFallback />}>
              <TodoList filter={filter} />
            </Suspense>
          </ErrorBoundary>
        </div>
      );
    }

    function NotFound() {
      const [, navigate] = useLocation();
      return (
        <div className="flex flex-col items-center gap-4 py-8">
          <p className="text-4xl font-bold">404</p>
          <p className="text-muted-foreground">Page not found</p>
          <Button variant="outline" onClick={() => navigate("/")}>Go home</Button>
        </div>
      );
    }

    // ── App ──────────────────────────────────────────────────────

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: 1 },
      },
    });

    function App() {
      return (
        <QueryClientProvider client={queryClient}>
          <div className="min-h-screen flex items-center justify-center p-4">
            <Card className="w-full max-w-lg">
              <CardHeader>
                <CardTitle>Todos</CardTitle>
                <CardDescription>A simple todo list backed by FastAPI</CardDescription>
              </CardHeader>
              <CardContent>
                <RouteSwitch>
                  <Route path="/">{() => <TodoPage filter="all" />}</Route>
                  <Route path="/active">{() => <TodoPage filter="active" />}</Route>
                  <Route path="/done">{() => <TodoPage filter="done" />}</Route>
                  <Route><NotFound /></Route>
                </RouteSwitch>
              </CardContent>
            </Card>
          </div>
        </QueryClientProvider>
      );
    }

    createRoot(document.getElementById("root")!).render(<App />);
  </script>
</body>
</html>
"""


@app.get("/{path:path}", response_class=HTMLResponse)
async def spa(path: str):
    return HTML

# ── Inline Tests ──────────────────────────────────────────────────────

def test_todo_toggle():
    todo = Todo("Buy milk")
    assert not todo.done
    todo.toggle_done()
    assert todo.done
    todo.toggle_done()
    assert not todo.done


def test_repo_add_and_list():
    repo = SqliteTodoRepository(db_path=":memory:")
    repo.add(Todo("First"))
    repo.add(Todo("Second"))
    todos = repo.list_all()
    assert len(todos) == 2
    assert todos[0].description == "First"
    assert todos[1].description == "Second"


def test_repo_get_by_index():
    repo = SqliteTodoRepository(db_path=":memory:")
    repo.add(Todo("Only"))
    todo = repo.get_by_index(0)
    assert todo.description == "Only"


def test_repo_toggle_and_save():
    repo = SqliteTodoRepository(db_path=":memory:")
    repo.add(Todo("Task"))
    todo = repo.get_by_index(0)
    assert not todo.done
    todo.toggle_done()
    repo.save(todo)
    reloaded = repo.get_by_index(0)
    assert reloaded.done


# ── CLI ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind host")
@click.option("--port", default=8765, type=int, help="Bind port")
def main(host: str, port: int | None):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import pytest
        sys.exit(pytest.main([__file__] + sys.argv[2:]))
    main()
