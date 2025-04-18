import { GraphCategory } from '$lib/enums';
import { icons } from '$lib/icons';
import type { Menu } from '$lib/types';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = () => {
  const menus: Menu[] = [
    {
      title: 'nav.workflows.title',
      routes: [
        {
          title: 'nav.workflows.templates',
          path: '/workflows/templates',
          icon: icons.appStore
        },
        {
          title: 'nav.workflows.graphs',
          path: '/workflows/graphs',
          icon: icons.documentFlowchart
        }
      ]
    },
    {
      title: 'nav.workflows.instances',
      routes: Object.entries(GraphCategory).map(([value, { label, icon }]) => ({
        title: label,
        path: `/workflows/instances/${value}`,
        icon: icon
      }))
    }
  ];
  return { menus };
};
