<script lang="ts">
	import styles from './Release.module.scss';
	import CategoryList from '@/features/changelog/components/CategoryList/CategoryList.svelte';
	import type { TRelease } from '@/features/changelog/types';

	export let release: TRelease;
</script>

<div class={styles.release}>
	<div class={styles.header}>
		<span class={styles.version}>v{release.version}</span>
		<span class={styles.date}>{release.date}</span>
	</div>
	<div class={styles.categories}>
		<CategoryList {release} />
	</div>
</div>
