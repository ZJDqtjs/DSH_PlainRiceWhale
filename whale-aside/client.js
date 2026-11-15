window.__ModuleLoader__.load({
  id: 'dsh-whale-aside',
  factory(require) {
    const React = require('react');
    const h = React.createElement;

    /** Mood key -> Chinese chip label (persona LANG_ZH_CN_ONLY: these strings stay Chinese). */
    const MOOD_LABELS = {
      tsun: '傲娇',
      sweet: '甜',
      lazy: '懒',
      shy: '害羞',
      panic: '慌',
      hungry: '想吃米饭',
      smug: '得意',
      meh: '无语',
    };

    /** Mood key -> chip emoji; unknown moods fall back to a neutral whale. */
    const MOOD_EMOJI = {
      tsun: '🐳',
      sweet: '🐳',
      lazy: '🐳',
      shy: '🐳',
      panic: '🐳',
      hungry: '🍚',
      smug: '🐳',
      meh: '🙄',
    };

    /** Mood key -> speech rate; a lazy whale drawls and a panicking one gabbles. */
    const MOOD_RATE = {
      tsun: 1.15,
      sweet: 1.08,
      lazy: 0.92,
      shy: 1.0,
      panic: 1.3,
      hungry: 1.1,
      smug: 1.2,
      meh: 0.95,
    };

    /** Mood key -> speech pitch; higher reads as younger and more emotive. */
    const MOOD_PITCH = {
      tsun: 1.45,
      sweet: 1.6,
      lazy: 1.3,
      shy: 1.5,
      panic: 1.55,
      hungry: 1.4,
      smug: 1.4,
      meh: 1.25,
    };

    /** localStorage key holding this browser's voice-override preference. */
    const VOICE_PREF_KEY = 'dsh.whale-aside.voice';

    /** Window event broadcast when the effective voice or an engine failure changes. */
    const VOICE_EVENT = 'whale-aside:voice';

    /**
     * Voice overrides this browser may send to the Host route. Every field is
     * optional: an empty voice with null prosody means "follow the Host
     * settings", so the picker never pins a value the Host would own.
     */
    const VOICE_PREF_DEFAULT = { voice: '', basePitchHz: null, baseRatePct: null, useEdge: true };

    /** Edge TTS Chinese voices offered in the picker: label -> wire name. */
    const VOICE_CHOICES = [
      ['晓伊·活泼（社区基准）', 'zh-CN-XiaoyiNeural'],
      ['晓晓·温暖', 'zh-CN-XiaoxiaoNeural'],
      ['云夏·奶音', 'zh-CN-YunxiaNeural'],
      ['云希·阳光', 'zh-CN-YunxiNeural'],
      ['云健·热血', 'zh-CN-YunjianNeural'],
      ['云扬·新闻腔', 'zh-CN-YunyangNeural'],
      ['晓北·东北话', 'zh-CN-liaoning-XiaobeiNeural'],
      ['晓妮·陕西话', 'zh-CN-shaanxi-XiaoniNeural'],
      ['晓辰·台湾腔', 'zh-TW-HsiaoChenNeural'],
      ['晓雨·台湾腔', 'zh-TW-HsiaoYuNeural'],
      ['云哲·台湾男声', 'zh-TW-YunJheNeural'],
      ['跟随宿主配置', ''],
    ];

    /** The fixed line the picker speaks while auditioning a new timbre. */
    const SAMPLE_LINE = '哼，才不是胖鲸鱼呢。主人要是想换个嗓子，就把这个名字改掉就好啦。';

    /** localStorage key holding the mute preference ('1' muted / '0' unmuted). */
    const MUTE_KEY = 'dsh.whale-aside.muted';

    /** Window event broadcast to every mounted bubble when mute flips. */
    const MUTE_EVENT = 'whale-aside:mute';

    /** Prefix route the Host half serves the mood stickers from (`assets/gifs/`). */
    const GIF_BASE = '/whale-aside/assets/gifs/';

    /**
     * Moods that ship a sticker, mapped to the file name under {@link GIF_BASE}.
     *
     * Mirrors `MOOD_STICKERS` in the Host half, which builds the route whitelist from
     * the same list. A mood absent here renders no `<img>` at all: the seven GIFs that
     * used to back `tsun`…`smug` are retired material, and their moods stay in the tool
     * and the voice prosody, so the absence must be silent rather than a 404.
     */
    const STICKER_ASSETS = {
      meh: 'meme2_clean.png',
    };

    /**
     * Cache-buster appended to every sticker URL. The asset route answers with
     * `cache-control: public, max-age=3600`, so a rebuilt sticker would otherwise keep
     * serving the old bytes from the browser cache for an hour. Bump this whenever the
     * files under `assets/gifs/` are regenerated, added to, removed, or change format
     * — '6' covers retiring the GIF set and shipping `meme2_clean.png` for `meh`.
     */
    const GIF_VERSION = '6';

    /**
     * Host route that synthesizes an aside with Edge TTS and returns its URL.
     * `POST` yields `{ ok, url, voice, pitch, rate }`; the MP3 is then served
     * from the same prefix, so one <audio> element per page is enough.
     */
    const VOICE_ROUTE = '/whale-aside/voice';

    /** Resting state when the mute preference cannot be read. */
    const DEFAULT_MUTED = false;

    /**
     * Scoped styles. Surfaces and text use only --dsw-alias-* theme tokens; the
     * literal colors below are artwork (the whale fluke inline SVG).
     */
    const WHALE_ASIDE_CSS = `
      .dsh-whale-aside-root {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 8px;
        margin: 4px 0;
        padding: 2px 0 2px 2px;
        max-width: 100%;
        min-width: 0;
        font-size: var(--dsh-content-font-size, 14px);
        line-height: calc(22px + var(--dsh-content-font-delta, 0px));
      }
      .dsh-whale-aside-tail {
        flex: none;
        width: 34px;
        height: 34px;
        margin-top: 3px;
        transform-origin: 50% 88%;
        animation: dsh-whale-aside-wag 2.8s ease-in-out infinite;
      }
      .dsh-whale-aside-tail > svg {
        display: block;
        width: 34px;
        height: 34px;
      }
      .dsh-whale-aside-bubble {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
        max-width: min(560px, 100%);
        padding: 8px 12px 9px;
        border: 1px solid var(--dsw-alias-border-l1);
        border-radius: 14px 14px 14px 4px;
        background: var(--dsw-alias-bg-layer-1);
        animation: dsh-whale-aside-float 4.5s ease-in-out infinite;
      }
      .dsh-whale-aside-head {
        display: flex;
        align-items: center;
        gap: 6px;
        min-width: 0;
      }
      .dsh-whale-aside-caption {
        flex: none;
        color: var(--dsw-alias-label-secondary);
        font-size: var(--dsh-content-font-size-secondary, 12px);
        line-height: 16px;
        letter-spacing: 0.04em;
      }
      .dsh-whale-aside-mood {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        flex: none;
        padding: 0 6px;
        border: 1px solid var(--dsw-alias-border-l2);
        border-radius: 999px;
        background: var(--dsw-alias-bg-layer-2);
        color: var(--dsw-alias-label-secondary);
        font-size: var(--dsh-content-font-size-secondary, 12px);
        line-height: 16px;
      }
      .dsh-whale-aside-mute {
        margin-left: auto;
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        padding: 0;
        border: 1px solid var(--dsw-alias-border-l2);
        border-radius: 999px;
        background: var(--dsw-alias-bg-layer-2);
        color: var(--dsw-alias-label-secondary);
        font-size: 11px;
        line-height: 1;
        cursor: pointer;
      }
      .dsh-whale-aside-mute:hover {
        background: var(--dsw-alias-interactive-bg-hover);
        color: var(--dsw-alias-label-primary);
      }
      .dsh-whale-aside-mute:focus-visible {
        outline: 2px solid var(--dsw-alias-brand-primary);
        outline-offset: 1px;
      }
      .dsh-whale-aside-body {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 10px;
        min-width: 0;
      }
      .dsh-whale-aside-lines {
        display: flex;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
        flex: 1 1 auto;
      }
      .dsh-whale-aside-gif {
        display: block;
        flex: none;
        width: auto;
        height: 84px;
        max-width: 120px;
        border-radius: 10px;
        background: transparent;
        object-fit: contain;
      }
      .dsh-whale-aside-text {
        color: var(--dsw-alias-label-primary);
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        cursor: pointer;
      }
      .dsh-whale-aside-text:hover {
        color: var(--dsw-alias-label-primary);
        text-decoration: underline dotted var(--dsw-alias-border-l3);
        text-underline-offset: 3px;
      }
      .dsh-whale-aside-text:focus-visible {
        outline: 2px solid var(--dsw-alias-brand-primary);
        outline-offset: 2px;
        border-radius: 4px;
      }
      .dsh-whale-aside-text[data-error="true"] {
        color: var(--dsw-alias-label-secondary);
        font-style: italic;
        cursor: default;
      }
      .dsh-whale-aside-typing {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 20px;
        color: var(--dsw-alias-label-secondary);
      }
      .dsh-whale-aside-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--dsw-alias-brand-primary);
        opacity: 0.35;
        animation: dsh-whale-aside-dot 1.1s ease-in-out infinite;
      }
      .dsh-whale-aside-dot:nth-child(2) {
        animation-delay: 0.18s;
      }
      .dsh-whale-aside-dot:nth-child(3) {
        animation-delay: 0.36s;
      }
      @keyframes dsh-whale-aside-wag {
        0%, 100% { transform: rotate(-4deg); }
        50% { transform: rotate(5deg); }
      }
      @keyframes dsh-whale-aside-float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-1px); }
      }
      @keyframes dsh-whale-aside-dot {
        0%, 100% { opacity: 0.3; transform: translateY(0); }
        50% { opacity: 1; transform: translateY(-2px); }
      }
      .dsh-whale-aside-engine {
        font-size: 11px;
        line-height: 16px;
        padding: 0 6px;
        border-radius: 8px;
        border: 1px solid var(--dsw-alias-border-neutral-primary, rgba(128, 128, 128, 0.35));
        color: var(--dsw-alias-text-secondary, inherit);
        background: transparent;
        cursor: pointer;
        white-space: nowrap;
      }
      .dsh-whale-aside-engine[data-engine="edge"] {
        color: var(--dsw-alias-text-link, inherit);
      }
      .dsh-whale-aside-engine[data-engine="sys"],
      .dsh-whale-aside-engine[data-engine="wait"] {
        color: var(--dsw-alias-text-state-warning, inherit);
      }
      .dsh-whale-aside-panel {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 6px;
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid var(--dsw-alias-border-neutral-primary, rgba(128, 128, 128, 0.35));
        font-size: 12px;
        line-height: 18px;
        color: var(--dsw-alias-text-primary, inherit);
      }
      .dsh-whale-aside-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
      }
      .dsh-whale-aside-panel select,
      .dsh-whale-aside-panel input {
        font: inherit;
        color: inherit;
        background: var(--dsw-alias-background-canvas, transparent);
        border: 1px solid var(--dsw-alias-border-neutral-primary, rgba(128, 128, 128, 0.35));
        border-radius: 6px;
        padding: 1px 4px;
      }
      .dsh-whale-aside-panel input[data-field="pitch"],
      .dsh-whale-aside-panel input[data-field="rate"] {
        width: 68px;
      }
      .dsh-whale-aside-panel input[data-field="voice"] {
        width: 208px;
      }
      .dsh-whale-aside-panel button {
        font: inherit;
        color: inherit;
        background: var(--dsw-alias-fill-secondary, transparent);
        border: 1px solid var(--dsw-alias-border-neutral-primary, rgba(128, 128, 128, 0.35));
        border-radius: 6px;
        padding: 1px 8px;
        cursor: pointer;
      }
      .dsh-whale-aside-note {
        color: var(--dsw-alias-text-secondary, inherit);
      }
      @media (prefers-reduced-motion: reduce) {
        .dsh-whale-aside-tail,
        .dsh-whale-aside-bubble,
        .dsh-whale-aside-dot {
          animation: none;
        }
        .dsh-whale-aside-dot {
          opacity: 0.6;
        }
        .dsh-whale-aside-gif:not([data-static="true"]) {
          display: none;
        }
      }
    `;

    /** Original inline artwork: a whale fluke with a small shine and a water drop. */
    const WHALE_TAIL = h('svg', {
      viewBox: '0 0 48 48',
      width: 34,
      height: 34,
      role: 'presentation',
      focusable: 'false',
      'aria-hidden': 'true',
    }, [
      h('path', {
        key: 'fluke',
        d: 'M24 44 C 19 36 12 27 5 18 C 3.5 16 5 13 7.5 13.5 C 9 13.8 10 14.5 11 16 C 15.5 22 20 27 24 31 C 28 27 32.5 22 37 16 C 38 14.5 39 13.8 40.5 13.5 C 43 13 44.5 16 43 18 C 36 27 29 36 24 44 Z',
        fill: '#3f86c9',
      }),
      h('path', {
        key: 'shine',
        d: 'M24 40 C 21 34 17 29 12 23',
        fill: 'none',
        stroke: '#9fd0f2',
        strokeWidth: 2.2,
        strokeLinecap: 'round',
      }),
      h('circle', {
        key: 'drop',
        cx: 35.5,
        cy: 9.5,
        r: 2.4,
        fill: '#bfe6ff',
      }),
    ]);

    /** Empty derivation used when a slot render receives no Tool block at all. */
    const EMPTY_ASIDE = { phase: 'unknown', typing: true, text: '', mood: '', isError: false };

    /* ------------------------------------------------------------------ *
     * Web Speech: module-level so one bubble's mute state and one callId
     * play-once ledger cover the whole page lifetime, not one component.
     * ------------------------------------------------------------------ */

    /** callIds whose aside already spoke on this page; replay by click is separate. */
    const played = new Set();

    /** Voice name fragments that read as a soft female Mandarin voice. */
    const PREFERRED_VOICE_NAME = /Xiaoxiao|Xiaoyi|Huihui|Yaoyao|女|female/i;

    /** A Mandarin (Mainland) or generic Chinese language tag. */
    const CHINESE_LANGUAGE = /^zh([-_]CN)?$/i;

    /** Text still waiting for the asynchronous `voiceschanged` delivery. */
    let pendingSpeech = null;

    /** The single `voiceschanged` listener registered while speech is pending. */
    let pendingListener = null;

    /** Read the mute preference; a missing or unreadable storage means unmuted. */
    function readMuted() {
      try {
        if (typeof window === 'undefined' || !window.localStorage) return DEFAULT_MUTED;
        return window.localStorage.getItem(MUTE_KEY) === '1';
      } catch (error) {
        return DEFAULT_MUTED;
      }
    }

    /** Persist the mute preference; storage may be unavailable in a sandboxed frame. */
    function writeMuted(muted) {
      try {
        if (typeof window === 'undefined' || !window.localStorage) return;
        window.localStorage.setItem(MUTE_KEY, muted === true ? '1' : '0');
      } catch (error) {
        /* the preference simply does not survive this session. */
      }
    }

    /** The browser synthesizer, or null when this environment has none. */
    function speechEngine() {
      try {
        if (typeof window === 'undefined') return null;
        const engine = window.speechSynthesis;
        return engine !== null && typeof engine === 'object' && typeof engine.speak === 'function' ? engine : null;
      } catch (error) {
        return null;
      }
    }

    /** The utterance constructor, or null when the Web Speech API is absent. */
    function utteranceType() {
      try {
        if (typeof window === 'undefined') return null;
        const Utterance = window.SpeechSynthesisUtterance;
        return typeof Utterance === 'function' ? Utterance : null;
      } catch (error) {
        return null;
      }
    }

    /**
     * Speech text for one aside: drop parenthetical stage directions (both the
     * fullwidth and the ASCII form) so the whale does not read them aloud.
     * @param text - the displayed aside.
     * @returns the speakable line, possibly empty.
     */
    function speechTextFor(text) {
      if (typeof text !== 'string') return '';
      try {
        return text
          .replace(/（[^）]*）/g, ' ')
          .replace(/\([^)]*\)/g, ' ')
          .replace(/\s+/g, ' ')
          .trim();
      } catch (error) {
        return '';
      }
    }

    /** Rate and pitch for a mood, with unknown moods on the neutral settings. */
    function prosodyFor(mood) {
      const known = typeof mood === 'string' && Object.prototype.hasOwnProperty.call(MOOD_RATE, mood) === true;
      const rate = known ? MOOD_RATE[mood] : 1;
      const pitch = known ? MOOD_PITCH[mood] : 1.4;
      return {
        rate: Math.min(3, Math.max(0.1, rate)),
        pitch: Math.min(2, Math.max(0, pitch)),
      };
    }

    /**
     * Choose a Chinese voice: a preferred female name first, then any zh voice,
     * then whatever the platform offers.
     * @param voices - the platform voice list.
     * @returns the selected voice, or null when the list is empty.
     */
    function pickVoice(voices) {
      const list = Array.isArray(voices) ? voices : [];
      const chinese = [];
      for (let index = 0; index < list.length; index += 1) {
        const voice = list[index];
        if (voice !== null && typeof voice === 'object' && typeof voice.lang === 'string' && CHINESE_LANGUAGE.test(voice.lang)) {
          chinese.push(voice);
        }
      }
      for (let index = 0; index < chinese.length; index += 1) {
        const voice = chinese[index];
        if (typeof voice.name === 'string' && PREFERRED_VOICE_NAME.test(voice.name)) return voice;
      }
      if (chinese.length > 0) return chinese[0];
      return list.length > 0 && list[0] !== null && typeof list[0] === 'object' ? list[0] : null;
    }

    /** Drop the pending line and detach its listener, so no stale voice fires. */
    function clearPending() {
      pendingSpeech = null;
      const engine = speechEngine();
      const listener = pendingListener;
      pendingListener = null;
      if (engine === null || listener === null) return;
      try {
        engine.removeEventListener('voiceschanged', listener);
      } catch (error) {
        /* an engine without listener removal simply keeps one dead callback. */
      }
    }

    /** Bumped on every new line so a slow synthesis cannot play over a newer one. */
    let speechToken = 0;

    /** The single audio element used for Host-synthesized clips. */
    let voiceAudio = null;

    /** Lazily create the shared audio element; null when the page has no Audio. */
    function audioElement() {
      if (voiceAudio !== null) return voiceAudio;
      try {
        if (typeof window === 'undefined' || typeof window.Audio !== 'function') return null;
        voiceAudio = new window.Audio();
        voiceAudio.preload = 'auto';
        return voiceAudio;
      } catch (error) {
        return null;
      }
    }

    /** Stop whatever clip is playing and release its source. */
    function stopAudio() {
      const audio = voiceAudio;
      if (audio === null) return;
      try {
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
      } catch (error) {
        /* an audio element that never started has nothing to stop. */
      }
    }

    /** Stop whatever is being spoken and forget any queued line. */
    function cancelSpeech() {
      speechToken += 1;
      clearPending();
      clearGesture();
      stopAudio();
      const engine = speechEngine();
      if (engine === null) return;
      try {
        engine.cancel();
      } catch (error) {
        /* cancelling an idle engine is a no-op some builds still reject. */
      }
    }

    /** Speak one clean line with the mood's prosody; never throws. */
    function speakNow(clean, mood) {
      const engine = speechEngine();
      const Utterance = utteranceType();
      if (engine === null || Utterance === null) return;
      try {
        const utterance = new Utterance(clean);
        const prosody = prosodyFor(mood);
        utterance.lang = 'zh-CN';
        utterance.rate = prosody.rate;
        utterance.pitch = prosody.pitch;
        let voices = [];
        try {
          voices = typeof engine.getVoices === 'function' ? engine.getVoices() : [];
        } catch (error) {
          voices = [];
        }
        const voice = pickVoice(voices);
        if (voice !== null) {
          try {
            utterance.voice = voice;
          } catch (error) {
            /* a platform voice that cannot be assigned keeps the default. */
          }
          if (typeof voice.lang === 'string' && voice.lang !== '') utterance.lang = voice.lang;
        }
        engine.speak(utterance);
      } catch (error) {
        /* speech is a bonus: a refusing engine must never break the bubble. */
      }
    }

    /** Read this browser's voice overrides; unreadable means follow the Host. */
    function readVoicePref() {
      try {
        if (typeof window === 'undefined' || !window.localStorage) return VOICE_PREF_DEFAULT;
        const raw = window.localStorage.getItem(VOICE_PREF_KEY);
        if (typeof raw !== 'string' || raw === '') return VOICE_PREF_DEFAULT;
        const parsed = JSON.parse(raw);
        if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) return VOICE_PREF_DEFAULT;
        return {
          voice: typeof parsed.voice === 'string' ? parsed.voice.trim().slice(0, 64) : '',
          basePitchHz: typeof parsed.basePitchHz === 'number' && Number.isFinite(parsed.basePitchHz)
            ? Math.max(-100, Math.min(100, Math.round(parsed.basePitchHz)))
            : null,
          baseRatePct: typeof parsed.baseRatePct === 'number' && Number.isFinite(parsed.baseRatePct)
            ? Math.max(-40, Math.min(40, Math.round(parsed.baseRatePct)))
            : null,
          useEdge: parsed.useEdge !== false,
        };
      } catch (error) {
        return VOICE_PREF_DEFAULT;
      }
    }

    /** Persist this browser's voice overrides; storage may simply be unavailable. */
    function writeVoicePref(pref) {
      try {
        if (typeof window === 'undefined' || !window.localStorage) return;
        window.localStorage.setItem(VOICE_PREF_KEY, JSON.stringify(pref));
      } catch (error) {
        /* the preference then lives only for this page. */
      }
    }

    /** What actually spoke last, so the badge can tell 主人 the truth. */
    let voiceStatus = { engine: 'idle', detail: '' };

    /** Publish the speaking engine and its detail to every mounted bubble. */
    function setVoiceStatus(engine, detail) {
      voiceStatus = { engine: String(engine), detail: typeof detail === 'string' ? detail.slice(0, 400) : '' };
      try {
        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function' && typeof window.CustomEvent === 'function') {
          window.dispatchEvent(new window.CustomEvent(VOICE_EVENT, { detail: voiceStatus }));
        }
      } catch (error) {
        /* the bubble that spoke updates itself regardless of the broadcast. */
      }
    }

    /** Play one synthesized clip: 'played' | 'stale' | 'blocked' | 'error'. */
    async function playUrl(url, token) {
      const audio = audioElement();
      if (audio === null) return 'error';
      try {
        audio.src = url;
        await audio.play();
        return token === speechToken ? 'played' : 'stale';
      } catch (error) {
        const name = error !== null && typeof error === 'object' ? error.name : '';
        return name === 'NotAllowedError' ? 'blocked' : 'error';
      }
    }

    /** A clip the browser will not autoplay yet, waiting for one real gesture. */
    let gestureClip = null;

    /** Drop the queued clip and its listeners; nothing replays on its own. */
    function clearGesture() {
      gestureClip = null;
      try {
        document.removeEventListener('click', onFirstGesture, true);
        document.removeEventListener('keydown', onFirstGesture, true);
      } catch (error) {
        /* a page without a document never queued anything. */
      }
    }

    /** The first gesture after a block replays the Host clip, same timbre. */
    function onFirstGesture() {
      const url = gestureClip;
      clearGesture();
      if (url === null || readMuted()) return;
      void playUrl(url, speechToken);
    }

    /** Queue a blocked clip instead of switching to the system voice. */
    function queueGesture(url) {
      gestureClip = url;
      try {
        document.addEventListener('click', onFirstGesture, true);
        document.addEventListener('keydown', onFirstGesture, true);
      } catch (error) {
        gestureClip = null;
      }
      setVoiceStatus('edge', '音频已经做好了，但浏览器不让自动播放：点一下页面就出声');
    }

    /**
     * Ask the Host half to synthesize this line with Edge TTS.
     * @param clean - the speakable line.
     * @param mood - the aside mood key.
     * @param prefIn - overrides to send, defaulting to the stored preference.
     * @returns `{ url, voice, pitch, rate }` on success, `{ error }` when the
     * Host answered badly, or null when the route cannot be reached at all.
     */
    async function requestClip(clean, mood, prefIn) {
      if (typeof window === 'undefined' || typeof window.fetch !== 'function') return null;
      const pref = prefIn !== null && typeof prefIn === 'object' ? prefIn : readVoicePref();
      const body = { text: clean, mood };
      if (pref.voice !== '') body.voice = pref.voice;
      if (pref.basePitchHz !== null) body.basePitchHz = pref.basePitchHz;
      if (pref.baseRatePct !== null) body.baseRatePct = pref.baseRatePct;
      if (pref.useEdge === false) body.enabled = false;
      try {
        const response = await window.fetch(VOICE_ROUTE, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body),
        });
        let payload = null;
        try {
          payload = await response.json();
        } catch (error) {
          payload = null;
        }
        if (response.ok && payload !== null && typeof payload === 'object' && payload.ok === true && typeof payload.url === 'string') {
          return {
            url: payload.url,
            voice: typeof payload.voice === 'string' ? payload.voice : '',
            pitch: typeof payload.pitch === 'string' ? payload.pitch : '',
            rate: typeof payload.rate === 'string' ? payload.rate : '',
          };
        }
        const detail = payload !== null && typeof payload === 'object' && typeof payload.error === 'string'
          ? payload.error
          : '宿主路由返回 HTTP ' + response.status;
        return { error: detail };
      } catch (error) {
        return { error: '宿主路由不可达：' + (error && error.message ? error.message : String(error)) };
      }
    }

    /**
     * Deliver one Host synthesis attempt: play the clip, queue it when the
     * browser blocks autoplay, or fall back to the system voice — and say out
     * loud, through the badge, which one actually talked.
     * @param clean - the speakable line.
     * @param mood - the aside mood key.
     * @param result - what `requestClip` answered.
     * @param token - the speech generation this line still owns.
     */
    function deliver(clean, mood, result, token) {
      if (token !== speechToken) return;
      if (result === null) {
        setVoiceStatus('sys', '宿主路由不可达（这个页面连不上 /whale-aside/voice）');
        speakBrowser(clean, mood);
        return;
      }
      if (typeof result.url === 'string') {
        setVoiceStatus('edge', 'Edge TTS：' + result.voice + ' ' + result.pitch + ' ' + result.rate);
        void playUrl(result.url, token).then((outcome) => {
          if (outcome === 'played' || outcome === 'stale') return;
          if (token !== speechToken) return;
          if (outcome === 'blocked') {
            queueGesture(result.url);
            return;
          }
          setVoiceStatus('sys', '宿主给了音频，但浏览器放不出来');
          speakBrowser(clean, mood);
        });
        return;
      }
      setVoiceStatus('sys', '系统音色兜底：' + (result.error || '宿主合成失败'));
      speakBrowser(clean, mood);
    }

    /**
     * Speak an aside once. Prefers the Host's Edge TTS clip; only a synthesis
     * or playback failure switches to the browser voice, and an autoplay block
     * waits for a gesture instead of changing the timbre behind 主人's back.
     * Muted, empty, or engine-less calls stay silent.
     * @param text - the displayed aside.
     * @param mood - the aside mood key.
     */
    function speakLine(text, mood) {
      if (readMuted()) return;
      const clean = speechTextFor(text);
      if (clean === '') return;
      const token = ++speechToken;
      setVoiceStatus('wait', '正在让宿主合成…');
      void requestClip(clean, mood).then((result) => {
        deliver(clean, mood, result, token);
      });
    }

    /** Audition one set of overrides with the sample line, ignoring the mute. */
    function previewVoice(mood, prefIn) {
      const key = typeof mood === 'string' && Object.prototype.hasOwnProperty.call(MOOD_RATE, mood) === true ? mood : 'tsun';
      const token = ++speechToken;
      setVoiceStatus('wait', '试听中…');
      void requestClip(SAMPLE_LINE, key, prefIn).then((result) => {
        deliver(SAMPLE_LINE, key, result, token);
      });
    }

    /** Ask the Host for the sample line using this browser's stored settings. */
    function previewVoiceStored() {
      previewVoice('tsun', null);
    }

    /** Parse one picker number field; blank or junk means "no override". */
    function numberOrNothing(value) {
      if (typeof value !== 'string') return null;
      const trimmed = value.trim();
      if (trimmed === '') return null;
      const parsed = Number(trimmed);
      return Number.isFinite(parsed) ? Math.round(parsed) : null;
    }

    /** `zh-CN-XiaoyiNeural …` -> `Xiaoyi`, for the little badge. */
    function shortVoiceName(detail) {
      const text = typeof detail === 'string' ? detail : '';
      const found = /([A-Za-z]+)Neural/.exec(text);
      if (found !== null) return found[1];
      return text === '' ? '' : text.slice(0, 24);
    }

    /** Short, honest label for whatever spoke last. */
    function describeEngine(status) {
      const engine = status !== null && typeof status === 'object' ? String(status.engine) : 'idle';
      if (engine === 'edge') return 'Edge·' + shortVoiceName(status.detail);
      if (engine === 'sys') return '浏览器系统音';
      if (engine === 'wait') return '合成中…';
      return '未发声';
    }

    /**
     * Browser fallback: speak through the platform voice, waiting once for the
     * asynchronous voice list when the engine has not delivered it yet.
     * @param clean - the speakable line.
     * @param mood - the aside mood key.
     */
    function speakBrowser(clean, mood) {
      const engine = speechEngine();
      if (engine === null || utteranceType() === null) return;

      let voices = [];
      try {
        voices = typeof engine.getVoices === 'function' ? engine.getVoices() : [];
      } catch (error) {
        voices = [];
      }
      if (Array.isArray(voices) && voices.length > 0) {
        speakNow(clean, mood);
        return;
      }

      clearPending();
      pendingSpeech = { clean, mood };
      const onVoicesChanged = () => {
        const entry = pendingSpeech;
        clearPending();
        if (entry === null || readMuted()) return;
        speakNow(entry.clean, entry.mood);
      };
      pendingListener = onVoicesChanged;
      try {
        engine.addEventListener('voiceschanged', onVoicesChanged);
      } catch (error) {
        clearPending();
      }
    }

    /**
     * Flip the shared mute preference, stop any current line when muting, and
     * tell every mounted bubble to redraw its icon.
     * @param muted - whether speech should now stay silent.
     */
    function applyMuted(muted) {
      writeMuted(muted);
      if (muted === true) cancelSpeech();
      try {
        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function' && typeof window.CustomEvent === 'function') {
          window.dispatchEvent(new window.CustomEvent(MUTE_EVENT, { detail: { muted: muted === true } }));
        }
      } catch (error) {
        /* the toggling bubble updates itself regardless of the broadcast. */
      }
    }

    /** Parse a raw argument JSON string without ever throwing. */
    function safeParse(raw) {
      if (typeof raw !== 'string' || raw.length === 0) return null;
      try {
        const value = JSON.parse(raw);
        return value !== null && typeof value === 'object' && Array.isArray(value) === false ? value : null;
      } catch (error) {
        return null;
      }
    }

    /** Read one field from the streaming argument view; partial arguments are expected. */
    function argsViewText(args, key) {
      if (args === null || typeof args !== 'object') return '';
      try {
        if (typeof args.text === 'function') {
          const value = args.text(key);
          if (typeof value === 'string') return value;
        }
      } catch (error) {
        return '';
      }
      return '';
    }

    /**
     * Trim the model's aside and drop a leaked「小声嘀咕：」wrapper; cap the
     * display length. A trailing「）」is only dropped when it closes a leaked
     * wrapper, so an aside that genuinely ends in a stage direction keeps it.
     */
    function normalizeWhaleText(value) {
      if (typeof value !== 'string') return '';
      let text = value.trim();
      let leaked = false;
      if (text.indexOf('（小声嘀咕：') === 0) {
        text = text.slice(6);
        leaked = true;
      } else if (text.indexOf('小声嘀咕：') === 0) {
        text = text.slice(5);
        leaked = true;
      }
      if (leaked === true && text.length > 0 && text.charAt(text.length - 1) === '）') text = text.slice(0, -1);
      return text.trim().slice(0, 240);
    }

    /**
     * Derive the bubble content from a Tool block at any lifecycle stage.
     * A settled block carries `kind` plus `call.argsRaw`; preparing/start blocks
     * carry phase/args/argsRaw. Every read is defensive: a throwing slot entry
     * would blank the whole chat row.
     * @param block - the Tool call block supplied by the slot owner.
     * @returns the normalized aside.
     */
    function deriveAside(block) {
      if (block === null || typeof block !== 'object') return EMPTY_ASIDE;

      const settled = Object.prototype.hasOwnProperty.call(block, 'kind') === true;
      const phase = settled ? 'settled' : block.phase === 'start' ? 'start' : 'preparing';

      let parsed = null;
      if (settled) {
        const call = block.call !== null && typeof block.call === 'object' ? block.call : null;
        parsed = call === null ? null : safeParse(call.argsRaw);
      } else {
        parsed = safeParse(block.argsRaw);
      }

      let text = parsed !== null && typeof parsed.text === 'string' ? parsed.text : '';
      let mood = parsed !== null && typeof parsed.mood === 'string' ? parsed.mood : '';
      if (text === '') text = argsViewText(block.args, 'text');
      if (mood === '') mood = argsViewText(block.args, 'mood');

      text = normalizeWhaleText(text);
      mood = typeof mood === 'string' ? mood.trim() : '';

      const isError = settled === true && block.isError === true;
      const typing = settled === false && text === '';
      if (settled === true && text === '') {
        text = isError ? '呜…这次的独白卡在喉咙里了…' : '（甩尾巴）';
      }

      return { phase, typing, text, mood, isError };
    }

    /** The mood's sticker image for a shipped mood and a non-preparing call, or null. */
    function renderSticker(mood, knownMood, phase) {
      if (knownMood !== true || phase === 'preparing') return null;
      const file = Object.prototype.hasOwnProperty.call(STICKER_ASSETS, mood) === true
        ? STICKER_ASSETS[mood]
        : null;
      if (file === null || typeof file !== 'string' || file === '') return null;
      // A PNG or JPG never animates, so the reduced-motion rule must not hide it.
      const isStatic = /\.(png|jpe?g)$/i.test(file) === true;
      return h('img', {
        key: 'gif',
        className: 'dsh-whale-aside-gif',
        src: GIF_BASE + file + '?v=' + GIF_VERSION,
        'data-static': isStatic === true ? 'true' : undefined,
        alt: '',
        loading: 'lazy',
        decoding: 'async',
        draggable: 'false',
        'aria-hidden': 'true',
        onError: (event) => {
          try {
            const target = event !== null && typeof event === 'object' ? event.currentTarget : null;
            if (target !== null && typeof target === 'object' && target.style !== undefined) target.style.display = 'none';
          } catch (error) {
            /* a missing sticker simply leaves the text bubble. */
          }
        },
      });
    }

    /** Render one whale-girl speech bubble for the `whale_aside` Tool call. */
    function WhaleAside(props) {
      const block = props === null || typeof props !== 'object' ? undefined : props.block;
      const aside = React.useMemo(() => deriveAside(block), [block]);

      /** Slot owner props: `callId` and the `preparing`/`start`/`result` discriminant. */
      const callId = props !== null && typeof props === 'object' && typeof props.callId === 'string' ? props.callId : '';
      const ownerPhase = props !== null && typeof props === 'object' && props.phase === 'result'
        ? 'result'
        : props !== null && typeof props === 'object' && props.phase === 'start' ? 'start' : 'preparing';

      const knownMood = Object.prototype.hasOwnProperty.call(MOOD_LABELS, aside.mood) === true;
      const moodLabel = knownMood ? MOOD_LABELS[aside.mood] : aside.mood;
      const moodEmoji = knownMood ? MOOD_EMOJI[aside.mood] : '🐳';

      const [muted, setMuted] = React.useState(() => readMuted());

      /** Who is actually speaking now, mirrored from the module-level status. */
      const [voice, setVoice] = React.useState(() => voiceStatus);

      /** This browser's voice overrides, editable in the picker. */
      const [pref, setPref] = React.useState(() => readVoicePref());

      /** Whether this bubble's voice picker is open. */
      const [pickerOpen, setPickerOpen] = React.useState(false);

      /** The lifecycle phase observed on the previous render; mount counts as seen. */
      const previousPhase = React.useRef(ownerPhase);

      /** A key unique to this call: the wire callId, or the text when it is absent. */
      const onceKey = callId !== '' ? callId : aside.text !== '' ? 'text:' + aside.text : '';

      /* Speak only on the observed non-result -> result transition. An aside that
         is already settled on mount (history, refresh, HMR) stays silent, and one
         callId never speaks twice on this page. Speaking and cancelling live in
         ONE effect so React always runs this cleanup before this setup: a
         separate cancel effect would race the line it is meant to protect. */
      React.useEffect(() => {
        const was = previousPhase.current;
        previousPhase.current = ownerPhase;
        const speaking = ownerPhase === 'result'
          && was !== 'result'
          && onceKey !== ''
          && played.has(onceKey) === false;
        if (speaking === true) {
          played.add(onceKey);
          speakLine(aside.text, aside.mood);
        }
        return () => cancelSpeech();
      }, [ownerPhase, onceKey, aside.text, aside.mood]);

      /* Every mounted bubble mirrors the shared mute preference. */
      React.useEffect(() => {
        const onMute = (event) => {
          const detail = event !== null && typeof event === 'object' ? event.detail : null;
          const next = detail !== null && typeof detail === 'object' && typeof detail.muted === 'boolean'
            ? detail.muted
            : readMuted();
          setMuted(next);
          if (next === true) cancelSpeech();
        };
        try {
          window.addEventListener(MUTE_EVENT, onMute);
        } catch (error) {
          return undefined;
        }
        setMuted(readMuted());
        return () => {
          try {
            window.removeEventListener(MUTE_EVENT, onMute);
          } catch (error) {
            /* a torn-down window has nothing left to detach from. */
          }
        };
      }, []);

      /* Every mounted bubble mirrors the shared voice status. */
      React.useEffect(() => {
        const onVoice = (event) => {
          const detail = event !== null && typeof event === 'object' ? event.detail : null;
          if (detail !== null && typeof detail === 'object') {
            setVoice({
              engine: typeof detail.engine === 'string' ? detail.engine : 'idle',
              detail: typeof detail.detail === 'string' ? detail.detail : '',
            });
            return;
          }
          setVoice(voiceStatus);
        };
        try {
          window.addEventListener(VOICE_EVENT, onVoice);
        } catch (error) {
          return undefined;
        }
        setVoice(voiceStatus);
        return () => {
          try {
            window.removeEventListener(VOICE_EVENT, onVoice);
          } catch (error) {
            /* a torn-down window has nothing left to detach from. */
          }
        };
      }, []);

      /** Merge one picker change into the preference and persist it at once. */
      const updatePref = React.useCallback((patch) => {
        setPref((current) => {
          const next = Object.assign({}, current, patch);
          writeVoicePref(next);
          return next;
        });
      }, []);

      /** Reset every override so the Host settings file owns the timbre again. */
      const followHost = React.useCallback(() => {
        updatePref({ voice: '', basePitchHz: null, baseRatePct: null, useEdge: true });
      }, [updatePref]);

      const toggleMute = React.useCallback(() => {
        applyMuted(readMuted() !== true);
      }, []);

      const replay = React.useCallback(() => {
        if (aside.text === '' || readMuted()) return;
        cancelSpeech();
        speakLine(aside.text, aside.mood);
      }, [aside.text, aside.mood]);

      const onTextKeyDown = React.useCallback((event) => {
        if (event === null || typeof event !== 'object') return;
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        replay();
      }, [replay]);

      const sticker = renderSticker(aside.mood, knownMood, aside.phase);

      /** The inline timbre picker: what speaks, and what 主人 can change. */
      const voicePanel = pickerOpen !== true
        ? null
        : h('div', { key: 'voice', className: 'dsh-whale-aside-panel' }, [
            h('div', { key: 'pick', className: 'dsh-whale-aside-row' }, [
              h('span', { key: 'lab', className: 'dsh-whale-aside-note' }, '音色'),
              h('select', {
                key: 'select',
                'aria-label': 'Edge TTS 音色',
                value: pref.voice,
                onChange: (event) => updatePref({
                  voice: event !== null && typeof event === 'object' && event.target !== null ? String(event.target.value) : '',
                }),
              }, VOICE_CHOICES.map((choice) => h('option', {
                key: choice[1] === '' ? 'host' : choice[1],
                value: choice[1],
              }, choice[0]))),
              h('input', {
                key: 'custom',
                'data-field': 'voice',
                type: 'text',
                'aria-label': '直接填音色名',
                placeholder: 'zh-CN-XiaoyiNeural',
                value: pref.voice,
                onChange: (event) => updatePref({
                  voice: event !== null && typeof event === 'object' && event.target !== null
                    ? String(event.target.value).trim().slice(0, 64)
                    : '',
                }),
              }),
            ]),
            h('div', { key: 'prosody', className: 'dsh-whale-aside-row' }, [
              h('span', { key: 'plab', className: 'dsh-whale-aside-note' }, '音高偏移 Hz'),
              h('input', {
                key: 'pitch',
                'data-field': 'pitch',
                type: 'number',
                min: -100,
                max: 100,
                step: 1,
                'aria-label': '音高偏移，赫兹；留空＝跟随宿主',
                placeholder: '默认',
                value: pref.basePitchHz === null ? '' : String(pref.basePitchHz),
                onChange: (event) => updatePref({
                  basePitchHz: event !== null && typeof event === 'object' && event.target !== null
                    ? numberOrNothing(String(event.target.value))
                    : null,
                }),
              }),
              h('span', { key: 'rlab', className: 'dsh-whale-aside-note' }, '语速偏移 %'),
              h('input', {
                key: 'rate',
                'data-field': 'rate',
                type: 'number',
                min: -40,
                max: 40,
                step: 1,
                'aria-label': '语速偏移，百分比；留空＝跟随宿主',
                placeholder: '默认',
                value: pref.baseRatePct === null ? '' : String(pref.baseRatePct),
                onChange: (event) => updatePref({
                  baseRatePct: event !== null && typeof event === 'object' && event.target !== null
                    ? numberOrNothing(String(event.target.value))
                    : null,
                }),
              }),
            ]),
            h('div', { key: 'flags', className: 'dsh-whale-aside-row' }, [
              h('label', { key: 'edge', className: 'dsh-whale-aside-note' }, [
                h('input', {
                  key: 'check',
                  type: 'checkbox',
                  checked: pref.useEdge === true,
                  onChange: (event) => updatePref({
                    useEdge: event !== null && typeof event === 'object' && event.target !== null && event.target.checked === true,
                  }),
                }),
                '用 Edge TTS（取消勾选＝只用浏览器音色）',
              ]),
            ]),
            h('div', { key: 'act', className: 'dsh-whale-aside-row' }, [
              h('button', {
                key: 'audition',
                type: 'button',
                onClick: () => previewVoice(aside.mood, pref),
              }, '试听这句'),
              h('button', {
                key: 'follow',
                type: 'button',
                onClick: followHost,
              }, '全部跟随宿主'),
            ]),
            h('div', {
              key: 'state',
              className: 'dsh-whale-aside-note',
            }, '现在发声：' + describeEngine(voice) + (voice.detail === '' ? '' : '（' + voice.detail + '）')),
            h('div', {
              key: 'hint',
              className: 'dsh-whale-aside-note',
            }, '这里的设置只影响本浏览器，立刻生效；全局默认在 ~/.dsh/whale-voice.json。'),
          ]);

      return h('div', {
        className: 'dsh-whale-aside-root',
        role: 'note',
        'aria-label': '鲸鱼娘的小独白',
        'data-phase': aside.phase,
        'data-mood': aside.mood === '' ? undefined : aside.mood,
      }, [
        h('style', { key: 'style' }, WHALE_ASIDE_CSS),
        h('div', {
          key: 'tail',
          className: 'dsh-whale-aside-tail',
          'aria-hidden': 'true',
        }, WHALE_TAIL),
        h('div', { key: 'bubble', className: 'dsh-whale-aside-bubble' }, [
          h('div', { key: 'head', className: 'dsh-whale-aside-head' }, [
            h('span', { key: 'caption', className: 'dsh-whale-aside-caption' }, '小独白'),
            moodLabel === ''
              ? null
              : h('span', { key: 'mood', className: 'dsh-whale-aside-mood' }, [
                  h('span', { key: 'emoji', 'aria-hidden': 'true' }, moodEmoji),
                  h('span', { key: 'label' }, moodLabel),
                ]),
            h('button', {
              key: 'engine',
              className: 'dsh-whale-aside-engine',
              type: 'button',
              'data-engine': voice.engine,
              title: voice.detail === '' ? '点我调整鲸鱼娘的音色' : voice.detail,
              'aria-expanded': pickerOpen === true ? 'true' : 'false',
              onClick: () => setPickerOpen(pickerOpen !== true),
            }, describeEngine(voice)),
            h('button', {
              key: 'mute',
              className: 'dsh-whale-aside-mute',
              type: 'button',
              'aria-label': muted ? '语音开' : '语音关',
              'aria-pressed': muted ? 'true' : 'false',
              title: muted ? '语音开' : '语音关',
              onClick: toggleMute,
            }, muted ? '🔇' : '🔊'),
          ]),
          h('div', { key: 'body', className: 'dsh-whale-aside-body' }, [
            h('div', { key: 'lines', className: 'dsh-whale-aside-lines' }, [
              aside.typing
                ? h('span', {
                    key: 'typing',
                    className: 'dsh-whale-aside-typing',
                    role: 'status',
                    'aria-label': '鲸鱼娘正在小声嘀咕…',
                  }, [
                    h('span', { key: 'dot1', className: 'dsh-whale-aside-dot' }),
                    h('span', { key: 'dot2', className: 'dsh-whale-aside-dot' }),
                    h('span', { key: 'dot3', className: 'dsh-whale-aside-dot' }),
                  ])
                : h('span', {
                    key: 'text',
                    className: 'dsh-whale-aside-text',
                    role: 'button',
                    tabIndex: 0,
                    title: '再听一次',
                    'aria-label': '再听一次',
                    'data-error': aside.isError ? 'true' : undefined,
                    onClick: replay,
                    onKeyDown: onTextKeyDown,
                  }, aside.text),
            ]),
            sticker,
            voicePanel,
          ]),
        ]),
      ]);
    }

    return {
      inject: ['slots'],
      apply(ctx) {
        ctx.slots.inject('tool.call.toolview', () => ctx.slots.register({
          name: 'tool.call.toolview',
          key: 'whale_aside',
        }, WhaleAside));
      },
    };
  },
});
