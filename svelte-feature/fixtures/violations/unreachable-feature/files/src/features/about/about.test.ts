import { expect, test } from 'vitest';
import { ABOUT } from '@/features/about';

test('has text', () => {
	expect(ABOUT.text).toBe('About us');
});
