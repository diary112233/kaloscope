<script lang="ts" module>
  export type RatingProps = {
    /** The rating score to display. */
    score?: number | null;
    /** The number of decimal places to show. */
    decimals?: number;
    /** The class names for the rating badge. */
    class?: string;
  };
</script>

<script lang="ts">
  let { score, decimals = 1, class: _class }: RatingProps = $props();
</script>

{#if score !== null && score !== undefined}
  <span class="rounded-sm bg-black/60 px-1 text-yellow-500 opacity-80 text-stroke {_class}">
    {Number(score).toFixed(decimals)}
  </span>
{/if}
