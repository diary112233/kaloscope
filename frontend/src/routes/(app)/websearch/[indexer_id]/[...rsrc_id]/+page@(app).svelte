<script lang="ts">
  import { page } from '$app/state';
  import { api } from '$lib/api';
  import { Overlay, VideoPlayer } from '$lib/components';
  import { createLoading } from '$lib/helpers';
  import type { Resource, Resp, Section } from '$lib/types';
  import { onMount, tick } from 'svelte';
  import { queryParameters, ssp } from 'sveltekit-search-params';

  // the URL query parameters
  const query = queryParameters(
    {
      section_id: ssp.string(),
      media_type: ssp.string(),
      video_type: ssp.string()
    },
    {
      pushHistory: false
    }
  );

  // the websearch result
  let resource: Resource | null = $state(null);
  let mediaType: string | null = $derived.by(() => resource?.media_type ?? query.media_type);
  let videoType: string | null = $derived.by(() => resource?.video_type ?? query.video_type);

  // the video player instance
  let player: VideoPlayer | null = $state(null);
  let refreshKey: number = $state(0);

  // the loading state
  const loading = createLoading();

  /**
   * Fetch the details of the resource.
   *
   * @param refresh - Whether to refresh the player.
   */
  function details(refresh: boolean = false) {
    loading.start();
    api
      .post(`flow/graph/${page.params.indexer_id}/execute`, {
        json: {
          $start: 'details_start',
          id: page.params.rsrc_id,
          section_id: query.section_id
        }
      })
      .json<Resp<Resource>>()
      .then((resp) => {
        refresh && (refreshKey = new Date().getTime());
        tick().then(() => onload(resp.data));
      })
      .finally(() => {
        loading.end();
      });
  }

  /**
   * Handle the resource load event.
   *
   * @param rsrc - The resource object.
   */
  function onload(rsrc: Resource) {
    resource = rsrc;
    const sections = rsrc?.sections ?? [];
    if (rsrc?.url) {
      if (mediaType === 'video' && player) {
        player.mount({
          url: rsrc.url,
          videoType: videoType,
          danmakus: rsrc.danmakus,
          sections: sections,
          sectionId: query.section_id,
          sectionChange: onchange,
          definitions: rsrc.definitions,
          title: rsrc.title,
          uploader: rsrc.uploader,
          uploadedAt: rsrc.uploaded_at
        });
      }
    } else if (sections.length > 0) {
      onchange(sections[0]);
    }
  }

  /**
   * Handle the section change event.
   *
   * @param section - The section object.
   */
  function onchange(section: Section) {
    if (section.url) {
      // switch the resource URL
      if (mediaType === 'video' && player) {
        player.mount({ next: !section.definition, url: section.url });
      }
    } else if (section.id && section.id !== query.section_id) {
      // update the query parameter and request the new section
      query.section_id = section.id;
      details(true);
    }
  }

  onMount(() => {
    details();
  });
</script>

<div class="history-back fixed inset-0 layer-1 max-sm:bottom-(--ks-dock-h)">
  <Overlay black loading={$loading} />
  {#key refreshKey}
    <VideoPlayer bind:this={player} />
  {/key}
</div>
