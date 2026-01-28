<script lang="ts">
  import { Image } from '$lib/components';
  import { icons } from '$lib/icons';
  import type { FlowGraph } from '$lib/types';

  let { graph, imgClass }: { graph: FlowGraph; imgClass?: string } = $props();
  const nameClass = 'mb-2 flex max-w-fit items-center gap-1 [&_*]:-mb-1';
</script>

<Image transparent src={graph.icon} icon={icons.documentFlowchart} class={imgClass} />
<div class="truncate">
  {#if graph.tmpl && !graph.editable}
    <a
      class="border-b border-transparent text-primary hover:border-primary/80 {nameClass}"
      title={graph.name}
      href={graph.tmpl.repo.repo_url}
      target="_blank"
    >
      <iconify-icon icon={icons.link}></iconify-icon>
      <span class="truncate">{graph.name}</span>
    </a>
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
