import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import Greeting from '@/features/welcome/components/Greeting/Greeting.svelte';
import { DEFAULT_GREETING } from '@/features/welcome';

test('shows the greeting', () => {
	render(Greeting, { greeting: DEFAULT_GREETING });
	expect(screen.getByRole('heading', { name: DEFAULT_GREETING.title })).toBeTruthy();
});
