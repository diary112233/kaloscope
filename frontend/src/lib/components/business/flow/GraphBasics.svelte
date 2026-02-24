<script lang="ts">
  import { Image, confirm } from '$lib/components';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';
  import type { FlowGraph } from '$lib/types';

  let {
    graph,
    imgClass,
    onupdate
  }: {
    graph: FlowGraph;
    imgClass?: string;
    onupdate?: (graph: FlowGraph) => void;
  } = $props();

  const nameClass = 'mb-2 flex max-w-fit items-center gap-1 [&_*]:-mb-1';
</script>

<Image transparent src={graph.icon} icon={icons.documentFlowchart} class={imgClass} />
<div class="truncate">
  {#if graph.tmpl && !graph.editable}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div
      tabindex="0"
      role="button"
      class="{graph.newest_tmpl ? 'hover-link' : 'pb-px'} {nameClass}"
      title={graph.name}
      onclick={() => {
        if (!graph.newest_tmpl) {
          return;
        }
        confirm({
          icon: icons.arrowBigUp,
          message: $_('flow.tmpl.confirm_update'),
          onconfirm: () => onupdate?.(graph)
        });
      }}
    >
      <iconify-icon icon={icons.link}></iconify-icon>
      <span class="truncate">{graph.name}</span>
    </div>
  {:else if !graph.editable}
    <div class="opacity-70 {nameClass}" title={graph.name}>
      <iconify-icon icon={icons.unlink}></iconify-icon>
      <span class="truncate">{graph.name}</span>
    </div>
  {:else}
    <div class={nameClass} title={graph.name}>
      <span class="truncate">{graph.name}</span>
    </div>
  {/if}
  <div class="truncate text-xs opacity-50" title={graph.description}>{graph.description}</div>
</div>
