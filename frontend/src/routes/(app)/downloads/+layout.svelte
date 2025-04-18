<script lang="ts">
  import { Drawer, Menu } from '$lib/components';
  import { onMount, type Snippet } from 'svelte';
  import type { LayoutData } from './$types';

  let { data, children }: { data: LayoutData; children: Snippet } = $props();

  let downloading: string = $state('');
  let completed: string = $state('');
  let upSpeed: string = $state('0 B');
  let dlSpeed: string = $state('0 B');

  let interpolation = $derived({
    'nav.downloads.downloading': downloading,
    'nav.downloads.completed': completed,
    'nav.downloads.speed.up': upSpeed,
    'nav.downloads.speed.dl': dlSpeed
  });

  onMount(() => {
    const eventSource = new EventSource('/_api/download/stats');
    eventSource.onmessage = function (event) {
      var stats = JSON.parse(event.data);
      downloading = stats.downloading;
      completed = stats.completed;
      upSpeed = stats.up_speed;
      dlSpeed = stats.dl_speed;
    };
    return () => eventSource.close();
  });
</script>

<Drawer>
  {@render children()}
  {#snippet side()}
    <Menu menus={data.menus} {interpolation} />
  {/snippet}
</Drawer>
