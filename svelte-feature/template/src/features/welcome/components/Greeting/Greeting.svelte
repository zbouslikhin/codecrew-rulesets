<script lang="ts">
	import styles from './Greeting.module.scss';
	import type { TGreeting } from '@/features/welcome/types';

	let { greeting }: { greeting: TGreeting } = $props();
</script>

<div class={styles.greeting}>
	<h1 class={styles.title}>{greeting.title}</h1>
	<p class={styles.subtitle}>{greeting.subtitle}</p>
</div>
