import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import Release from '@/features/changelog/components/Release/Release.svelte';

test('shows the version and date', () => {
	render(Release, { release: { version: '1.2.3', date: '2026-09-01', categories: [] } });
	expect(screen.getByText('v1.2.3')).toBeTruthy();
	expect(screen.getByText('2026-09-01')).toBeTruthy();
});
