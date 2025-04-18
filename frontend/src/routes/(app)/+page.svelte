<script lang="ts">
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores';

  goto($user?.preferences?.homepage ?? '/dashboard');
</script>
