<script lang="ts" module>
  export type SignpostsProps = {
    /** The class names for the signposts. */
    class?: string;
  };
</script>

<script lang="ts">
  import { _ } from '$lib/i18n';
  import { signposts } from '$lib/stores';

  let { class: _class }: SignpostsProps = $props();
</script>

{#if $signposts.length > 0}
  <div class="flex items-baseline gap-1 truncate px-2 {_class}">
    {#each $signposts as signpost, index (index)}
      {@const last = index === $signposts.length - 1}
      <span class="font-medium text-content/90 {last ? 'truncate' : 'opacity-90'}">{$_(signpost, [''])}</span>
      {#if !last}
        <span class="font-title opacity-40">&gt;</span>
      {/if}
    {/each}
  </div>
{/if}
