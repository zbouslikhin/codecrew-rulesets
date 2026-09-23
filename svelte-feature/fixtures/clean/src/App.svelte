<script lang="ts">
	import { RELEASES } from '@/features/changelog';
	import Release from '@/features/changelog/components/Release/Release.svelte';
</script>

{#each RELEASES as release (release.version)}
	<Release {release} />
{/each}
