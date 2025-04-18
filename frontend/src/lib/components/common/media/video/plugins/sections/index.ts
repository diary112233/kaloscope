import { icons, iconToSVG } from '$lib/icons';
import type { Section } from '$lib/types';
import OptionList from 'xgplayer/es/plugins/common/optionList';
import OptionsIcon from 'xgplayer/es/plugins/common/optionsIcon';
import './index.css';

type AttrObject = {
  [key: string]: string | number | undefined;
  index?: number;
};

type ChangeData = {
  from: AttrObject | null;
  to: AttrObject;
};

type DelegateEvent = Event & {
  delegateTarget: Element;
};

export default class Sections extends OptionsIcon {
  static get pluginName() {
    return 'sections';
  }

  static get defaultConfig() {
    return {
      ...OptionsIcon.defaultConfig,
      className: 'xgplayer-sections',
      isShowIcon: true,
      heightLimit: false,
      hidePortrait: false,
      sectionId: '',
      sectionChange: () => {}
    };
  }

  get isDefinition() {
    return (this.config.list as Section[]).some((item) => item.definition);
  }

  onIconClick = () => {
    const plugin = this.player.getPlugin('playbackRate');
    if (plugin && plugin.optionsList && plugin.isActive) {
      plugin.optionsList.hide();
      plugin.isActive = false;
    }
  };

  onItemClick = (event: DelegateEvent, data: ChangeData) => {
    super.onItemClick(event, data);
    if (typeof this.config.sectionChange === 'function') {
      this.config.sectionChange({
        id: data.to.id,
        url: data.to.url,
        title: data.to.showText,
        definition: data.to.definition === 'true'
      });
    }
  };

  registerIcons() {
    return {
      sections: {
        icon: iconToSVG(this.isDefinition ? icons.shadow : icons.listCheck),
        class: 'size-6 text-white/80'
      }
    };
  }

  afterCreate() {
    super.afterCreate();
    this.renderItemList();
    if (this.isDefinition) {
      this.on('url_change', (url: string) => {
        this.player.config.url = url;
        this.renderItemList();
      });
    }
  }

  renderItemList() {
    const { config, optionsList, player } = this;

    this.curIndex = -1;
    const items = (config.list as Section[]).map((item, index) => {
      const sectionItem = {
        id: item.id || '',
        url: item.url || '',
        showText: item.title,
        definition: item.definition || false,
        selected: (item.id || item.url) === (config.sectionId || player.config.url || '')
      };
      if (sectionItem.selected) {
        this.curIndex = index;
      }
      return sectionItem;
    });

    if (optionsList) {
      optionsList.renderItemList(items);
    } else {
      const isSide = config.listType === 'side';
      this.optionsList = new OptionList({
        root: isSide ? player.innerContainer || player.root : this.root,
        config: {
          data: items || [],
          className: isSide ? 'xg-right-side xg-side-list xgplayer-sections' : '',
          domEventType: 'click',
          onItemClick: this.onItemClick
        }
      });
      this.show();
    }
  }

  show() {
    if (this.config.list && this.config.list.length > 0) {
      super.show();
    }
  }

  destroy() {
    super.destroy();
  }
}
