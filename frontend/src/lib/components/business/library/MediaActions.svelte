<script lang="ts" module>
  import type { MediaItem, MediaProgressStatus, MediaProgressStatusResult } from '$lib/types';
  import type { IconifyIcon } from 'iconify-icon';
  import type { MouseEventHandler } from 'svelte/elements';

  export type MediaActionsProps = {
    item: MediaItem;
    class?: string;
    triggerClass?: string;
    onclick?: () => void;
    progressStatuses?: MediaProgressStatus[];
    onprogress?: (result: MediaProgressStatusResult) => void;
    onscrape?: () => void;
    ondelete?: () => void;
  };
</script>

<script lang="ts">
  import { Dropdown, MediaDelConfirm, MetadataScraper } from '$lib/components';
  import { closeDropdowns } from '$lib/components/common/interaction/Dropdown.svelte';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';
  import { mediaProgressStatus, setMediaProgressStatus } from '$lib/progress';
  import { user } from '$lib/stores';

  let {
    item,
    class: _class,
    triggerClass,
    onclick,
    progressStatuses = [],
    onprogress,
    onscrape,
    ondelete
  }: MediaActionsProps = $props();
  let scraper: MetadataScraper | null = $state(null);
  let deleter: MediaDelConfirm | null = $state(null);
  let changingProgress = $state(false);

  const progressIcons = {
    watching: icons.playCircle,
    watched: icons.checkmarkCircle,
    unwatched: icons.subtractCircle
  };

  async function changeProgress(status: MediaProgressStatus) {
    if (changingProgress || mediaProgressStatus(item.progress) === status) {
      return;
    }
    changingProgress = true;
    try {
      onprogress?.(await setMediaProgressStatus(item.id, status));
    } catch (error) {
      console.error(error);
    } finally {
      changingProgress = false;
    }
  }
</script>

{#snippet action(icon: IconifyIcon, text: string, onclick: MouseEventHandler<HTMLElement>, disabled: boolean = false)}
  <li>
    <button
      class="px-2"
      {disabled}
      onclick={(event) => {
        event.stopPropagation();
        closeDropdowns();
        onclick?.(event);
      }}
    >
      <iconify-icon {icon} width="1rem" class="size-4"></iconify-icon>
      {text}
    </button>
  </li>
{/snippet}

<Dropdown
  contentWidth="8rem"
  contentClass="shadow-lg!"
  class={_class}
  onclick={(event) => {
    event.stopPropagation();
    closeDropdowns(event.currentTarget);
    onclick?.();
  }}
>
  {#snippet trigger()}
    <div class="btn btn-circle border-0 btn-subtle btn-sm {triggerClass}">
      <iconify-icon icon={icons.moreVertical} width="1.25rem"></iconify-icon>
    </div>
  {/snippet}
  <ul class="menu gap-1">
    {#each progressStatuses as status}
      {@render action(
        progressIcons[status],
        $_(`media.progress.${status}`),
        () => changeProgress(status),
        changingProgress || mediaProgressStatus(item.progress) === status
      )}
    {/each}
    {#if progressStatuses.length && $user?.role === 'admin' && (onscrape || ondelete)}
      <li class="my-0.5 border-t border-base-content/10"></li>
    {/if}
    {#if $user?.role === 'admin' && onscrape}
      {@render action(icons.boxMultipleSearch, $_('action.scrape'), () => {
        // scrape metadata for the media item
        scraper?.showModal();
      })}
    {/if}
    {#if $user?.role === 'admin' && ondelete}
      {@render action(icons.delete, $_('action.delete'), () => {
        // show delete confirm dialog
        deleter?.showModal(item);
      })}
    {/if}
  </ul>
</Dropdown>

{#if $user?.role === 'admin' && onscrape}
  <MetadataScraper bind:this={scraper} {item} {onscrape} />
{/if}

{#if $user?.role === 'admin' && ondelete}
  <MediaDelConfirm bind:this={deleter} onconfirm={ondelete} />
{/if}
