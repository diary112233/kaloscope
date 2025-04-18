<script lang="ts">
  import { nodeFormatter } from '$lib/i18n';
  import type { Field } from '$lib/types';

  let field: Field = $props();
  const { label } = nodeFormatter;
</script>

<div class="divider mb-0 opacity-80">{$label(field.label)}</div>
