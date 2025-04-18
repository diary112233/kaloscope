<script lang="ts">
  import { page } from '$app/state';
  import { api } from '$lib/api';
  import { Overlay, VideoPlayer } from '$lib/components';
  import { createLoading } from '$lib/helpers';
  import type { MediaItem, Resp } from '$lib/types';
  import { onMount } from 'svelte';

  let item: MediaItem | null = $state(null);
  let player: VideoPlayer;

  // the loading state
  const loading = createLoading();

  onMount(() => {
    loading.start();
    api
      .get(`media/${page.params.item_id}`)
      .json<Resp<MediaItem>>()
      .then((resp) => {
        item = resp.data;
        player.mount({ url: `/_api/media/stream?path=${item.path}`, title: item?.name });
      })
      .finally(() => {
        loading.end();
      });
  });
</script>

<div class="history-back fixed inset-0 layer-1 max-sm:bottom-[var(--ks-dock-h)]">
  <Overlay black loading={$loading} />
  <VideoPlayer bind:this={player} />
</div>
