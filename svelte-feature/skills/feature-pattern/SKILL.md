---
name: feature-pattern
description: How a feature is laid out in this Svelte 5 + TypeScript architecture, file by file, with the code each file starts from. Read before you add a feature or a component.
---
# The feature pattern

Everything a feature needs lives in `src/features/<feature>/` (camelCase). The structure check
allows exactly these entries, and nothing else:

```
src/features/todoList/
  index.ts              what the feature offers to the rest of the app (required)
  types.ts              its types, T-prefixed (required)
  constants.ts          its constants
  components/           one folder per component
    TodoList/
      TodoList.svelte
      TodoList.module.scss
      TodoList.test.ts
  http/                 functions that call the backend
  stores/               state shared between its components
  *.test.ts             tests that aren't about one component
```

## The files

`types.ts`: type aliases start with `T` (the checks enforce it in `.ts` and `.svelte`):

```ts
export type TTodo = { id: number; text: string; done: boolean };
```

`components/TodoList/TodoList.svelte`: Svelte 5 runes, styles as a CSS module, imports across
folders with `@/`, never `../`:

```svelte
<script lang="ts">
	import styles from './TodoList.module.scss';
	import type { TTodo } from '@/features/todoList/types';

	let { todos = [] }: { todos?: TTodo[] } = $props();
	let open = $derived(todos.filter((t) => !t.done));
</script>

<ul class={styles.list}>
	{#each open as todo (todo.id)}
		<li>{todo.text}</li>
	{/each}
</ul>
```

`components/TodoList/TodoList.module.scss`: required next to every component, even if short.
Class names are local to the component; use them as `styles.<name>`.

`index.ts`: the only door into the feature. Other code imports from `@/features/todoList`, not
from files inside it:

```ts
export { default as TodoList } from '@/features/todoList/components/TodoList/TodoList.svelte';
export type { TTodo } from '@/features/todoList/types';
```

`components/TodoList/TodoList.test.ts`: every feature needs at least one test; a component test
that renders it and asserts what a user sees is the usual one:

```ts
import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import TodoList from '@/features/todoList/components/TodoList/TodoList.svelte';

test('lists the open todos', () => {
	render(TodoList, { todos: [{ id: 1, text: 'Write tests', done: false }] });
	expect(screen.getByText('Write tests')).toBeTruthy();
});
```

## A feature must be used

The reachability check follows imports from `src/main.ts`. A feature with passing tests that
nothing renders fails. Wire it in before you finish: import it (from its `index.ts`) in
`App.svelte` or in a feature that is already reachable. A type-only import doesn't count.

## What fails most often

- A helper file in the feature's root (`utils.ts`, `helpers.ts`): not allowed. Shared helpers go
  to `src/utils/`; feature-specific logic into `stores/`, `http/` or the component.
- A component file directly in `components/`: each component has its own folder, named like the
  component, in PascalCase.
- `../` in an import: use `@/`.
- A component without its `.module.scss`.
- `interface Todo` or `type Todo`: types are `type TTodo`.
- Editing a `*.generated.ts` file: those are produced by tools.
