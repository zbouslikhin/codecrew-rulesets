<script lang="ts">
	import { RELEASES } from '@/features/changelog';
	import Release from '@/features/changelog/components/Release/Release.svelte';
	import { ABOUT } from '@/features/about';
</script>

<p>{ABOUT.text}</p>
{#each RELEASES as release (release.version)}
	<Release {release} />
{/each}
