<script lang="ts">
	import styles from './CategoryList.module.scss';
	import type { TRelease } from '@/features/changelog/types';

	export let release: TRelease;
</script>

<ul class={styles.list}>
	{#each release.categories as category (category.name)}
		<li>{category.name}</li>
	{/each}
</ul>
