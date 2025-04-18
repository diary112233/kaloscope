<script lang="ts" module>
  import type { ViewMode, ViewModes } from '$lib/types';

  export type ViewSwitcherProps = {
    /** The supported view modes. */
    modes: ViewModes;
    /** The active view mode. */
    mode: ViewMode;
  };
</script>

<script lang="ts">
  import { Button } from '$lib/components';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';

  let { modes, mode = $bindable() }: ViewSwitcherProps = $props();
</script>

<!-- view mode switcher -->
{#if modes.length > 1}
  <span class="join rounded-field shadow-sm">
    {#each modes as m (m)}
      <Button
        ghost={false}
        icon={m === 'grid' ? icons.grid : icons.appsList}
        text={$_(`enum.view_mode.${m}`)}
        class="join-item {mode === m ? 'btn-active' : 'text-inactive'}"
        onclick={() => (mode = m)}
      />
    {/each}
  </span>
{/if}
