<script lang="ts">
  import { restoreRoute } from '$lib/stores';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  restoreRoute(data.menus[0]?.routes[0]?.path);
</script>
