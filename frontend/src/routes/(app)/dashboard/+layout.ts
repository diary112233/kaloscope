import { api } from '$lib/api';
import type { FlowGraph, Page, Resp } from '$lib/types';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => {
  let graphs: FlowGraph[] = [];

  await api
    .get('flow/graph/list', {
      searchParams: [
        ['page_num', 0],
        ['ordering', 'name'],
        ['category', 'indexer'],
        ['states', 'modified'],
        ['states', 'published']
      ]
    })
    .json<Resp<Page<FlowGraph>>>()
    .then((resp) => {
      const items = resp.data.items;
      graphs = items.filter((g) => g.node_types.includes('board_start'));
    });

  return { graphs };
};
