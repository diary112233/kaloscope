import { Plugin } from 'xgplayer';
import './index.css';

export default class Gradient extends Plugin {
  static get pluginName() {
    return 'gradient';
  }

  render() {
    return `
      <xg-gradient class="xgplayer-gradient top"></xg-gradient>
      <xg-gradient class="xgplayer-gradient bottom"></xg-gradient>
    `;
  }
}
