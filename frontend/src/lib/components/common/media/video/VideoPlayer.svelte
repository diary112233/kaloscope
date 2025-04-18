<script lang="ts" module>
  import type { Danmaku, Definition, Optional, Section } from '$lib/types';
  import type { IUrl } from 'xgplayer/es/defaultConfig';
  import type OptionsPlugin from 'xgplayer/es/plugins/common/optionsIcon';
  import type DanmakuPlugin from 'xgplayer/es/plugins/danmu';
  import type FullscreenPlugin from 'xgplayer/es/plugins/fullscreen';
  import type MobilePlugin from 'xgplayer/es/plugins/mobile';

  /**
   * The type of the video player properties.
   */
  export type VideoPlayerProps = {
    /** The width of the container. */
    width?: string;
    /** The height of the container. */
    height?: string;
  };

  /**
   * The type of the video options.
   */
  export type VideoOptions = {
    url: IUrl;
  } & Optional<{
    width: string | number;
    height: string | number;
    videoType: string;
    danmakus: Danmaku[];
    sections: Section[];
    sectionId: string;
    sectionChange: (section: Section) => void;
    definitions: Definition[];
    next: boolean;
    title: string;
    uploader: string;
    uploadedAt: string;
  }>;
</script>

<script lang="ts">
  import { isWhite, sniffer } from '$lib/utils';
  import { onMount, tick } from 'svelte';
  import { v4 as uuidv4 } from 'uuid';
  import Player, { Events, SimplePlayer } from 'xgplayer';
  import DefaultPreset from './plugins/preset';
  import VideoSettings from './VideoSettings.svelte';

  const { width = '100%', height = '100%' }: VideoPlayerProps = $props();
  const id: string = `player-${uuidv4()}`;
  let container: HTMLDivElement;
  let danmakuContainer: HTMLDivElement;
  let videoSettings: VideoSettings;

  let player: Player | null = $state(null);
  let mobilePlugin: MobilePlugin | null = $derived.by(() => player?.getPlugin('mobile'));
  let danmakuPlugin: DanmakuPlugin | null = $derived.by(() => player?.getPlugin('danmu'));
  let sectionsPlugin: OptionsPlugin | null = $derived.by(() => player?.getPlugin('sections'));
  let fullscreenPlugin: FullscreenPlugin | null = $derived.by(() => player?.getPlugin('fullscreen'));
  let playbackRatePlugin: OptionsPlugin | null = $derived.by(() => player?.getPlugin('playbackRate'));

  let themeColor: string | null = null;
  let screenLocked: boolean = $state(false);
  let rotateFullscreen: boolean = $state(false);

  /**
   * Toggles the fullscreen state of the player.
   *
   * https://h5player.bytedance.com/plugins/internalplugins/fullscreen.html#switchcallback
   */
  const toggleFullscreen = () => {
    if (!player || !fullscreenPlugin) {
      return;
    }
    if (player.isRotateFullscreen) {
      // exit rotate fullscreen mode
      player.exitRotateFullscreen();
      rotateFullscreen = player.isRotateFullscreen;
      fullscreenPlugin.animate(rotateFullscreen);
      toggleDanmakuDirection();
      videoSettings.toggleDirection();
    } else if (player.cssfullscreen) {
      // exit css fullscreen mode
      player.exitCssFullscreen();
      fullscreenPlugin.animate(player.cssfullscreen);
    } else if (player.fullscreen) {
      // exit native fullscreen mode
      player.exitFullscreen(container);
      if (screenLocked) {
        // unlock the screen orientation if it was locked
        fullscreenPlugin.unlockScreen();
        screenLocked = false;
      }
    } else {
      // enter fullscreen mode based on the device type and aspect ratio
      if (sniffer.isMobile() && player.aspectRatio > 1) {
        if (videoSettings.landscapeMode() === 'web_api' && !sniffer.isIos()) {
          // native fullscreen mode
          player.getFullscreen(container).catch(() => {});
          // try to lock the screen orientation
          fullscreenPlugin.lockScreen('landscape-primary');
          screenLocked = true;
        } else {
          // rotate fullscreen mode
          player.getRotateFullscreen();
          rotateFullscreen = player.isRotateFullscreen;
          fullscreenPlugin.animate(rotateFullscreen);
          toggleDanmakuDirection();
          videoSettings.toggleDirection();
        }
      } else if (sniffer.isIos()) {
        // css fullscreen mode
        player.getCssFullscreen(container);
        fullscreenPlugin.animate(player.cssfullscreen);
      } else {
        // native fullscreen mode
        player.getFullscreen(container).catch(() => {});
      }
    }
  };

  /**
   * Toggles the scroll direction of the danmaku.
   */
  const toggleDanmakuDirection = () => {
    tick().then(() => {
      const danmujs = danmakuPlugin?.danmujs;
      if (danmujs) {
        const portrait = screen.orientation.type.includes('portrait');
        const direction = portrait && rotateFullscreen ? 'b2t' : 'r2l';
        danmujs.stop();
        danmujs.setDirection(direction);
        danmujs.start();
        player?.paused && danmujs.pause();
      }
    });
  };

  /**
   * Formats the danmakus to the format required by the player.
   *
   * @param danmakus - The list of video comments.
   */
  const formatDanmakus = (danmakus: Danmaku[] | null | undefined) => {
    if (!danmakus || danmakus.length === 0) {
      return [];
    }
    return danmakus
      .filter((danmaku) => danmaku.text)
      .map(({ id, text, start, duration, mode, color }) => {
        return {
          id: id || uuidv4(),
          txt: text,
          start: start || 0,
          duration: duration || 5000,
          mode: mode || 'scroll',
          color: !!color && !isWhite(color),
          style: {
            color: color || '#fff'
          }
        };
      });
  };

  /**
   * Extracts the definitions from the video options.
   *
   * @param options - The video options.
   */
  const formatDefinitions = (options: VideoOptions): Definition[] => {
    if (options.definitions && options.definitions.length > 0) {
      return options.definitions.filter((d) => d.url && d.definition);
    }
    return [];
  };

  /**
   * Extracts the sections from the video options.
   *
   * @param options - The video options.
   */
  const formatSections = (options: VideoOptions): Section[] => {
    if (options.sections && options.sections.length > 0) {
      return options.sections
        .filter((s) => (s.id || s.url) && s.title)
        .map((s) => ({
          id: s.id,
          url: s.url,
          title: s.title,
          definition: false
        }));
    }
    return formatDefinitions(options).map((d) => ({
      id: null,
      url: d.url,
      title: String(d.definition),
      definition: true
    }));
  };

  /**
   * The playback rates available for the player.
   *
   * https://h5player.bytedance.com/plugins/internalplugins/playbackrate.html#list
   */
  const playbackRates = [
    { text: '2.0x', rate: 2.0 },
    { text: '1.5x', rate: 1.5 },
    { text: '1.25x', rate: 1.25 },
    { text: '1.0x', rate: 1.0, iconText: { en: '1.0x', zh: '倍速' } },
    { text: '0.75x', rate: 0.75 },
    { text: '0.5x', rate: 0.5 }
  ];

  /**
   * Mounts the player with the given options.
   *
   * @param options - The video options.
   */
  export function mount(options: VideoOptions) {
    if (!options || !options.url) {
      return;
    }
    // if the player is already mounted, just switch the URL
    if (player) {
      if (options.next) {
        player.playNext({ url: options.url });
      } else {
        videoSettings.changeDefinition(options.url);
      }
      return;
    }
    // create a new player instance
    SimplePlayer.defaultPreset = DefaultPreset;
    player = new SimplePlayer({
      id: id,
      url: options.url,
      width: options.width ?? width,
      height: options.height ?? height,
      videoType: options.videoType,
      definitions: formatDefinitions(options),
      danmu: {
        comments: formatDanmakus(options.danmakus),
        defaultOff: true,
        closeDefaultBtn: true,
        ext: {
          container: danmakuContainer
        }
      },
      topBar: {
        title: options.title,
        uploader: options.uploader,
        uploadedAt: options.uploadedAt,
        settingsModal: videoSettings
      },
      fullscreen: {
        switchCallback: toggleFullscreen
      },
      playbackRate: {
        index: 100,
        list: playbackRates
      },
      sections: {
        index: 99,
        list: formatSections(options),
        sectionId: options.sectionId,
        sectionChange: options.sectionChange
      },
      volume: {
        index: 98,
        default: 1,
        showValueLabel: true
      },
      mobile: {
        gradient: 'none',
        gestureX: false,
        disablePress: true
      },
      controls: {
        mode: 'normal',
        initShow: true
      },
      miniprogress: true,
      pip: true
    });
    // customize the player
    listenEvents(player);
    usePluginHooks(player);
    // initialize the settings
    videoSettings.init();
  }

  /**
   * Listens to player events and executes the corresponding actions.
   *
   * @param player - The player instance.
   */
  function listenEvents(player: Player) {
    [Events.FULLSCREEN_CHANGE, Events.CSS_FULLSCREEN_CHANGE].forEach((event) => {
      player.on(event, (fullscreen) => {
        // remove the width style to fix the resizing issue
        if (fullscreen && player.root) {
          player.root.style.width = '';
        }
        // update the theme color meta tag
        const metaTag = document.querySelector('meta[name="theme-color"]');
        if (metaTag) {
          if (fullscreen && themeColor === null) {
            themeColor = metaTag.getAttribute('content');
            metaTag.setAttribute('content', '#000');
          } else if (!fullscreen && themeColor) {
            metaTag.setAttribute('content', themeColor);
            themeColor = null;
          }
        }
      });
    });
    if (mobilePlugin) {
      // enable the gestures on mobile devices after the first play
      player.once(Events.PLAY, () => {
        mobilePlugin.config.gestureX = true;
        mobilePlugin.config.disablePress = false;
      });
      // disable the long press gesture when the player is paused
      player.on(Events.PAUSE, () => {
        mobilePlugin.config.disablePress = true;
      });
      player.on(Events.PLAY, () => {
        mobilePlugin.config.disablePress = false;
      });
      // fix the issue that the long press event is interrupted by the touchmove event
      player.on(Events.USER_ACTION, (data) => {
        if (data.pluginName === 'mobile' && data.eventType === 'press') {
          mobilePlugin.config.disablePress = true;
          mobilePlugin.config.disableGesture = true;
          player.config.enableSwipeHandler = () => {
            if (!player.paused) {
              mobilePlugin.config.disablePress = false;
              mobilePlugin.config.disableGesture = false;
              mobilePlugin.onPressEnd({});
            }
          };
        }
      });
    }
  }

  /**
   * Uses the plugin hooks to customize the player behavior.
   *
   * @param player - The player instance.
   */
  function usePluginHooks(player: Player) {
    player.usePluginHooks('mobile', 'videoClick', () => {
      if (player.isPlaying) {
        return true;
      }
      for (const plugin of [sectionsPlugin, playbackRatePlugin]) {
        if (plugin && plugin.optionsList && plugin.isActive) {
          plugin.optionsList.hide();
          plugin.isActive = false;
          return false;
        }
      }
      return true;
    });
  }

  /**
   * Handles the orientation change event.
   */
  function onorientationchange() {
    if (player?.isRotateFullscreen) {
      toggleDanmakuDirection();
      videoSettings.toggleDirection();
    }
  }

  onMount(() => {
    // add the event listener for orientation change on mobile devices
    const isMobile = sniffer.isMobile();
    if (isMobile) {
      window.addEventListener('orientationchange', onorientationchange);
    }
    return () => {
      // destroy the player instance
      player?.destroy();
      // remove the event listener
      if (isMobile) {
        window.removeEventListener('orientationchange', onorientationchange);
      }
      // recover the theme color meta tag
      if (themeColor) {
        const metaTag = document.querySelector('meta[name="theme-color"]');
        if (metaTag) {
          metaTag.setAttribute('content', themeColor);
        }
        themeColor = null;
      }
    };
  });
</script>

<!-- The video player container. -->
<div bind:this={container} class="relative" style:width style:height>
  <div {id}></div>
  <!-- The danmaku container. -->
  <div
    bind:this={danmakuContainer}
    class="pointer-events-none absolute inset-0 layer-0 !overflow-visible text-stroke"
    style:height={rotateFullscreen ? '100dvh' : '100%'}
    style:right={rotateFullscreen ? '32px' : '0'}
  ></div>
</div>
<!-- The video settings component. -->
<VideoSettings bind:this={videoSettings} {player} />

<style>
  :global {
    .xgplayer {
      font-family: unset !important;

      &.xgplayer-mobile {
        @media only screen and (orientation: portrait) {
          .xg-side-list.xg-right-side {
            width: 30%;
            right: -15%;
          }
          &.xgplayer-rotate-fullscreen {
            width: 100dvh;
            height: 100dvw;
            .xg-side-list.xg-right-side {
              width: 20%;
              right: -10%;
            }
          }
        }
        @media only screen and (orientation: landscape) {
          .xg-side-list.xg-right-side {
            width: 20%;
            right: -10%;
          }
          &.xgplayer-rotate-fullscreen {
            width: 100dvw;
            height: 100dvh;
          }
        }
      }

      &.xgplayer-is-fullscreen,
      &.xgplayer-is-cssfullscreen,
      &.xgplayer-rotate-fullscreen {
        .xg-mini-progress {
          display: none;
        }
      }

      &.xgplayer-isloading,
      &.xgplayer-playing {
        .xgplayer-start {
          display: none;
        }
      }

      &.xgplayer-nostart {
        .xg-top-bar {
          display: flex !important;
        }
      }

      &.xgplayer-inactive:not(.xgplayer-nostart) {
        .top-bar-autohide {
          display: flex !important;
          opacity: 0;
          visibility: hidden;
          pointer-events: none;
        }
      }

      .xg-top-bar {
        padding: 0 !important;
        height: 52px !important;
        left: 10px;
        right: 10px;
        cursor: default;
        pointer-events: auto;
        opacity: 1;
        visibility: visible;
        transition:
          opacity 0.5s ease,
          visibility 0.5s ease;
      }

      .xg-top-note {
        top: 56px !important;
        height: 28px !important;
        width: 96px !important;
        margin-left: -48px !important;
        background-color: hsla(0, 0%, 30%, 0.3) !important;
        span {
          height: 28px !important;
          line-height: 28px !important;
        }
      }

      .xgplayer-controls {
        .xg-tips {
          /* https://github.com/bytedance/xgplayer/issues/1460 */
          display: none !important;
        }
        cursor: default;
        background-image: initial !important;
      }

      .xgplayer-start {
        width: 70px !important;
        height: 70px !important;
        xg-start-inner {
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50% !important;
          background-color: hsla(0, 0%, 30%, 0.3) !important;
        }
      }

      .xgplayer-replay {
        xg-replay-txt {
          font-size: 18px !important;
          font-weight: 800;
          text-shadow: 0px 1px 1px rgba(0, 0, 0, 0.2);
        }
      }

      .xgplayer-volume {
        .xgplayer-value-label {
          border-top-left-radius: 2px;
          border-top-right-radius: 2px;
          background-color: hsla(0, 0%, 10%, 0.9);
        }
        .xgplayer-slider {
          border-bottom-left-radius: 2px;
          border-bottom-right-radius: 2px;
          background-color: hsla(0, 0%, 10%, 0.9);
        }
      }

      .xg-side-list {
        &.xg-options-list {
          opacity: 1;
          z-index: 11;
          font-size: 20px;
          font-family: var(--font-title);
          background-color: hsla(0, 0%, 10%, 0.9) !important;
        }
      }
    }
  }
</style>
