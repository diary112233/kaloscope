<script lang="ts">
  import { api } from '$lib/api';
  import { Button, Cell, DataView, HCell, Search, URLRuleEditor, confirm } from '$lib/components';
  import { createLoading } from '$lib/helpers';
  import { _, dateTime } from '$lib/i18n';
  import { icons } from '$lib/icons';
  import type { Resp, URLRule } from '$lib/types';
  import { debounce } from '$lib/utils';
  import { onMount, tick } from 'svelte';

  let rules: URLRule[] = $state([]);
  let pattern: string = $state('');
  let creator: URLRuleEditor | null = $state(null);
  let updater: URLRuleEditor | null = $state(null);
  let selected: URLRule | null = $state(null);
  const loading = createLoading();

  /**
   * Search for URL rules.
   */
  function search() {
    loading.start();
    api
      .get('network/rule/list', { searchParams: { pattern } })
      .json<Resp<URLRule[]>>()
      .then((resp) => (rules = resp.data))
      .finally(() => loading.end());
  }

  /**
   * Delete a URL rule by ID.
   *
   * @param id - The URL rule ID.
   */
  function del(id: number) {
    loading.start();
    api
      .post('network/rule/delete', { json: { ids: [id] } })
      .then(() => search())
      .catch(() => loading.end());
  }

  /**
   * Toggle a boolean field of a URL rule.
   *
   * @param rule - The URL rule.
   * @param field - The field to toggle.
   */
  function toggle(rule: URLRule, field: 'secure_dns' | 'http_proxy') {
    const value = !rule[field];
    rule[field] = value;
    api.post('network/rule/toggle', { json: { id: rule.id, [field]: value } });
  }

  /**
   * Sort the URL rules.
   */
  const sort = debounce(() => {
    const ids = rules.map((rule) => rule.id);
    api.post('network/rule/sort', { json: { ids } });
  });

  /**
   * Move a rule up in the list.
   *
   * @param index - The index of the rule to move up.
   */
  function moveUp(index: number) {
    if (index <= 0) {
      return;
    }
    const temp = rules[index];
    rules[index] = rules[index - 1];
    rules[index - 1] = temp;
    sort();
  }

  /**
   * Move a rule down in the list.
   *
   * @param index - The index of the rule to move down.
   */
  function moveDown(index: number) {
    if (index >= rules.length - 1) {
      return;
    }
    const temp = rules[index];
    rules[index] = rules[index + 1];
    rules[index + 1] = temp;
    sort();
  }

  onMount(() => {
    search();
  });
</script>

<DataView dvh loading={$loading} data={rules}>
  {#snippet filters()}
    <Search label={$_('field.pattern')} bind:value={pattern} onsearch={() => search()} />
  {/snippet}
  {#snippet actions()}
    <Button size="md" icon={icons.bookGlobe} text={$_('field.secure_dns')} />
    <Button size="md" icon={icons.serverLink} text={$_('field.http_proxy')} />
    <Button
      size="md"
      icon={icons.addCircle}
      text={$_('action.add', $_('entity.rule'))}
      onclick={() => creator?.showModal()}
    />
  {/snippet}
  {#snippet header()}
    <HCell width={['30%', '48%']} text={$_('field.pattern')} />
    <HCell width={['15%', '26%']} text={$_('field.secure_dns')} />
    <HCell width={['15%', '26%']} text={$_('field.http_proxy')} />
    <HCell width={['20%', null]} text={$_('field.created')} />
    <HCell width={['20%', null]} text={$_('field.updated')} />
    <HCell actions />
  {/snippet}
  {#snippet row(rule, index)}
    <Cell text={rule.pattern} />
    <Cell>
      <input
        type="checkbox"
        class="toggle toggle-sm"
        checked={rule.secure_dns}
        onchange={() => toggle(rule, 'secure_dns')}
      />
    </Cell>
    <Cell>
      <input
        type="checkbox"
        class="toggle toggle-sm"
        checked={rule.http_proxy}
        onchange={() => toggle(rule, 'http_proxy')}
      />
    </Cell>
    <Cell text={$dateTime(rule.created_at)} />
    <Cell text={$dateTime(rule.updated_at)} />
    <Cell
      actions={[
        {
          icon: icons.edit,
          text: $_('action.edit', $_('entity.rule')),
          onclick: () => {
            selected = rule;
            tick().then(() => updater?.showModal());
          }
        },
        {
          icon: icons.arrowUp,
          text: $_('action.move_up'),
          disabled: !!pattern || index === 0,
          onclick: () => moveUp(index)
        },
        {
          icon: icons.arrowDown,
          text: $_('action.move_down'),
          disabled: !!pattern || index === rules.length - 1,
          onclick: () => moveDown(index)
        },
        {
          icon: icons.deleteDismiss,
          text: $_('action.delete', $_('entity.rule')),
          onclick: () => {
            confirm({
              icon: icons.deleteDismiss,
              title: `${$_('action.delete', $_('entity.rule'))} [${rule.pattern}]`,
              onconfirm: () => del(rule.id)
            });
          }
        }
      ]}
    />
  {/snippet}
</DataView>

<URLRuleEditor bind:this={creator} onsave={() => search()} />

{#if selected}
  <URLRuleEditor bind:this={updater} {...selected} onsave={() => search()} />
{/if}
