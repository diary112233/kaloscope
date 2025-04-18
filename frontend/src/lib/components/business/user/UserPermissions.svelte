<script lang="ts">
  import { Modal } from '$lib/components';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  let { id }: { id?: string } = $props();

  let modal: Modal;
  export const showModal = () => modal.show();
</script>

<Modal icon={icons.personEdit} title={$_('action.assign_permissions')} bind:this={modal}></Modal>
