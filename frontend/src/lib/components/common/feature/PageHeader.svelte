<script lang="ts" module>
  import type { Snippet } from 'svelte';

  export type PageHeaderProps = {
    /** The header content snippet. */
    children?: Snippet;
    /** The fallback header content snippet. */
    fallback?: Snippet;
  };

  let header: Snippet | null = $state(null);
</script>

<script lang="ts">
  import { onMount } from 'svelte';

  let { children, fallback }: PageHeaderProps = $props();

  onMount(() => {
    // if children is provided, use it as the header snippet
    if (children) {
      header = children;
      return () => {
        header = null;
      };
    }
  });
</script>

<!-- if children is not provided, render the header snippet -->
{#if !children}
  {#if header}
    {@render header()}
  {:else if fallback}
    {@render fallback()}
  {/if}
{/if}
