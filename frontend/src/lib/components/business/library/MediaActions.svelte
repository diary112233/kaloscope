<script lang="ts" module>
  import type { MediaItem } from '$lib/types';

  export type MediaActionsProps = {
    item: MediaItem;
    class?: string;
    triggerClass?: string;
    ondelete?: () => void;
  };
</script>

<script lang="ts">
  import { api } from '$lib/api';
  import { Dropdown, confirm, mediaTitle } from '$lib/components';
  import { closeAll } from '$lib/components/common/interaction/Dropdown.svelte';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';

  let { item, class: _class, triggerClass, ondelete }: MediaActionsProps = $props();

  /**
   * Delete the media item.
   */
  function deleteItem() {
    confirm({
      icon: icons.delete,
      title: `${$_('action.delete')} [${mediaTitle(item)}]`,
      onconfirm: () => {
        api.post('media/delete', { json: { ids: [item.id] } }).then(() => ondelete?.());
      }
    });
  }
</script>

<Dropdown
  contentWidth="10rem"
  contentClass="shadow-lg!"
  class="dropdown-end {_class}"
  onclick={(event) => {
    closeAll();
    event.stopPropagation();
  }}
>
  {#snippet trigger()}
    <div class="btn btn-circle border-0 btn-subtle btn-sm {triggerClass}">
      <iconify-icon icon={icons.moreVertical} width="1.25rem"></iconify-icon>
    </div>
  {/snippet}
  <ul class="menu gap-1">
    <li>
      <button
        class="px-2"
        onclick={(event) => {
          event.stopPropagation();
          deleteItem();
          event.currentTarget.blur();
        }}
      >
        <iconify-icon icon={icons.delete} width="1rem"></iconify-icon>
        {$_('action.delete')}
      </button>
    </li>
  </ul>
</Dropdown>
