<script lang="ts">
	import styles from './CategoryList.module.scss';
	import type { TRelease } from '@/features/changelog/types';

	type Props = { release: TRelease };
	export let release: Props['release'];
</script>

<ul class={styles.list}>
	{#each release.categories as category (category.name)}
		<li>{category.name}</li>
	{/each}
</ul>
