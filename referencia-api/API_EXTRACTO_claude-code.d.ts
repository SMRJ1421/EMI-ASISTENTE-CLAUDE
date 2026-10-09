// EXTRACTO de la API de Claude Code 2.1.294 (claude-code/index.d.ts), solo lo relevante para el problema de tamaño de Emi.
// Archivo completo (614 KB, 15.202 líneas): C:/Users/Admin0011/.claude/dev-mods/da5e8c78-c252-4d1c-9f43-47016e40a9d5/mascota/.claude-plugin/types/claude-code/index.d.ts
// Cada bloque indica su rango de líneas en el archivo completo.

// ======== líneas 1742-1766: CommandPresentation: dónde se muestra la respuesta (fullscreen o pantalla principal) ========
  /**
   * Where a command's answer will show: which of the terminal's two layouts
   * the surface renders, and how wide it is when the command runs.
   *
   * A fact the engine stamps on `command.run`, so a command that draws (opens
   * a pane, prints a wide table) can suit the room it has: the fullscreen
   * layout docks a pane beside the transcript from 110 columns, the main
   * screen places it inline above the prompt at any width.
   */
  export type CommandPresentation = {
      /**
       * True under the fullscreen (alternate-screen) layout; false on the main
       * screen (`CLAUDE_CODE_NO_FLICKER=0`, tmux by default) and headless.
       *
       * The fact `RenderViewport`'s `isFullscreen` carries on every terminal
       * drawing, from the same source: the two agree.
       */
      isFullscreen: boolean;
      /**
       * The terminal's width in cells as the command runs; 80 where no terminal
       * has measured (headless with no tty).
       */
      columns: number;
  };


// ======== líneas 2330-2480: $.ui: toast, status, open (paneles), blit, invalidate, resolve ========
           *
           * @param tool_use_id the call whose open dialog gets the line
           * @param text the line to show; undefined removes it
           * @example
           * $.ui.notice(e.tool_use_id, "checked by my-plugin"); return next(e)
           */
          notice: (tool_use_id: string, text: string | undefined) => void;
          /**
           * Re-runs an event whose results the engine caches: `ui.render` draws the
           * instances this plugin may draw again; the others drop the cached answers.
           *
           * A render hook whose state changed (a countdown) calls it to redraw: ten a
           * second at most, thirty in the terminal for its shown pane, expanded band
           * and prompt hint (sooner calls fold); a cached answer: dropped next turn.
           *
           * @remarks For `ui.render`, the instances this plugin's matchers on it may
           *   select: one naming no `requestId`, every instance of its component.
           * @param event `ui.render`, or a cached-answer event: `prompt.section`,
           *   `prompt.context`, `prompt.attachment`, `tool/command/config.describe`
           */
          invalidate: (event: InvalidatableEventName) => void;
          /**
           * Repaints a mounted `Raster` this plugin's own render hook drew with new
           * cells, or swaps a keyed `Image` it drew to a new source; no redraw.
           *
           * The surface paints the cells or source at its next frame, so blits
           * between frames fold into one: up to 120 a second taken, some sixty
           * shown. An Image swap sends one small command; a resize is a redraw.
           *
           * @param args `requestId` (the site), `key`, and `cells` (RasterProps) or
           *             `source` (ImageSource); `columns`, `rows` (the mounted size)
           * @returns `{}` once the cells or source are its next frame, or `{ deny }`
           *          (not mounted, not this plugin's, another size, cells that do
           *          not decode, a bad source, or an Image drawing its alt there:
           *          no placeholder images, or a file this terminal cannot read)
           * @example
           * $.clock.every(33, () => $.ui.blit({ requestId, key, cells: frame() }))
           * @example
           * await $.ui.blit({ requestId: 'browser', key: 'view',
           *   source: { shm: name, format: 'rgb', width, height } })
           */
          blit: (args: UiBlitArgs) => Promise<UiBlitResult>;
          /**
           * The elements of the surface `e` is drawn on (Elements[e.surface]): a
           * frozen table of constructors, the JSX tags a render hook draws with.
           *
           * A read, not a dispatch: the engine ran `ui.resolve` (the other hooks,
           * then core) at load, per surface and component. Narrowed `e.surface`:
           * that table exactly; unnarrowed: the union, so shared names type-check.
           *
           * @param e this hook's own `ui.render` argument (its surface and
           *          component pick the table)
           * @returns the surface's frozen element table (`Elements[e.surface]`)
           * @example
           * const { Box, Text } = $.ui.resolve(e)
           * return <Box>{await next(e)}<Text dimColor>done</Text></Box>
           */
          resolve: <E extends ResolveInput>(e: E) => Elements[E['surface']];
          /**
           * Appends one line to the transcript, drawn like a system notice (dim;
           * not sent to the model), or with `{ to: "debug" }` to the debug log alone.
           *
           * A row of its own at the next frame, in logging order; a `-p` or SDK
           * host receives it as `ui_log`; the debug log has it either way, to 10000
           * characters. Raised as `ui.log`: a hook above may rewrite `e.to`.
           *
           * @param text the line's text, of any length: the terminal draws its
           *   first 2000 characters, a remote surface 10000
           * @param options `to`: `transcript` (the default) or `debug`
           * @example
           * $.ui.log(`prompt from ${e.origin.kind}: ${e.text.length} chars`)
           * @example
           * $.ui.log(`cache miss for ${e.tool_use_id}`, { to: "debug" })
           */
          log: (text: string, options?: UiLogOptions) => void;
          /**
           * Asks the user `question` in the engine's own AskUserQuestion dialog and
           * resolves to the label they chose, or the text typed under "Other".
           *
           * A `tool.call` of `AskUserQuestion` through every hook but the calling
           * one, drawn by `ui.render` on `AskUserQuestion`; a multi-select answer is
           * comma-joined. Rejects when dismissed, and in a `-p` run (no one to ask).
           *
           * @param question the question, ending in a question mark
           * @param options 2-4 option labels, or `{ options, header, multiSelect }`
           * @returns the label chosen, the chosen labels comma-joined, or free text
           *          typed under "Other" (so compare it with the labels exactly)
           * @example
           * const mood = await $.ui.ask("How careful?", ["Bold", "Careful"])
           */
          ask: (question: string, options?: readonly string[] | AskOptions) => Promise<string>;
          /**
           * Shows `text` for a few seconds under the plugin's name: a small box on
           * the stack of plugin toasts over the transcript's top right corner.
           *
           * A click takes it off, the pointer over it holds it. Where the transcript
           * is printed into scrollback (nothing to float over) it is one line on the
           * notification bar. It leaves the transcript and the model untouched.
           *
           * @remarks While the pane shown was opened `holdToasts`, by any plugin, it
           *   waits undrawn, its timer not started; past 50 waiting, an older leaves.
           * @param text the line to show, its first 2000 characters drawn (10000
           *   remotely); an unpaired surrogate half in it is drawn as U+FFFD
           * @param options `timeoutMs`: how long it stays (default 4000)
           * @example
           * $.ui.toast(`turn took ${Math.round(e.durationMs / 1000)} s`)
           */
          toast: (text: string, options?: ToastOptions) => void;
          /**
           * Pins `text` as this plugin's status line under the prompt, beside the
           * engine's own pinned notices, until the next call replaces it.
           *
           * One per plugin; `undefined` removes it.
           *
           * @param text the line to keep on screen, its first 2000 characters drawn
           *   (10000 remotely); undefined clears it
           * @example
           * $.ui.status("thinking..."); return next(e)
           */
          status: (text: string | undefined) => void;
          /**
           * Opens a pane, a framed region the surface places and this plugin draws
           * by hooking `ui.render` for `{ component: "Pane" }`; says if it is drawn.
           *
           * One per id (an open id retitles; a `ui.open` hook may refuse). Asked,
           * the person's command, prompt or press behind it (not `focus`), it is
           * placed at any width; unasked, from 144 columns, 110 for one once asked.
           *
           * @remarks Below that it waits undrawn (`$.ui.panes()`: `isPlaced` false)
           *   until they open it or the terminal widens; a `-p` run places all.
           * @param pane `id` (1-64 of letters, digits, `_`, `-`), `title`, `focus`,
           *   `closeOnEscape` and `holdToasts` (a dialog), `rows` / `columns` wanted
           * @returns `{ isPlaced: true }` once drawn (or retitled), else `{ isPlaced:
           *   false, reason }` (UiOpenResult); `dock` or `inline` is on `Pane` props
           * @example
           * await $.ui.open({ id: "clock", title: "Clock" })
           * @example
           * await $.ui.open({ id: "ask", focus: true, closeOnEscape: true, rows: 9 })
           * @example
           * const opened = await $.ui.open({ id: "clock" })
           * if (!opened.isPlaced) $.ui.toast("clock: widen the terminal to see it")
           */
          open: (pane: PaneOpenArgs) => Promise<UiOpenResult>;
          /**
           * Closes one of the open panes; an id that is not open is left alone.
           *
           * Every close raises `ui.close`, `e.origin` naming whose it is: this call
           * (`plugin`), the person's mark or key (`person`), an unload (`unload`).
           * A hook answering without `next` keeps the pane open, save on an unload.
           *
           * @param pane `id`: the id the pane was opened under

// ======== líneas 3755-3845: Elements: qué elementos dibuja cada superficie (Raster e Image solo en terminal; Svg en escritorio) ========
   */
  export type ElementConstructor<P> = (props: P & ElementChildren) => RenderElement;

  /**
   * Every element name of every surface: what a table handed out is completed to
   * (an omitted one draws a fragment; see `ui.resolve`).
   */
  export type ElementName = {
      [P in RenderSurface]: keyof Elements[P];
  }[RenderSurface];

  /**
   * The element constructors each surface draws, by `e.surface`: what
   * `$.ui.resolve(e)` returns and a `ui.resolve` hook passes on; no globals.
   *
   * All carry `Box`, `Text`, `Button`, `Link`, `Code`, `Markdown`; every remote
   * surface `Svg`; all but mobile `Input` and `Select`; terminal and desktop
   * `Client`; terminal `Raster` and `Image`. Narrowed on `e.surface`, that table.
   */
  export type Elements = {
      terminal: {
          Box: ElementConstructor<BoxProps>;
          Text: ElementConstructor<TextProps>;
          Button: ElementConstructor<ButtonProps>;
          Input: ElementConstructor<InputProps>;
          Select: ElementConstructor<SelectProps>;
          Link: ElementConstructor<LinkProps>;
          Code: ElementConstructor<CodeProps>;
          Markdown: ElementConstructor<MarkdownProps>;
          /**
           * A region one of the plugin's surface modules draws (ClientModule), named
           * by `module`: a string literal, the module's path relative to this file.
           *
           * The engine reads the surface module off the hooks module's source
           * before anything runs, so a variable, a template with a substitution or
           * a computed path as `module` is refused at load, naming the line.
           */
          Client: ElementConstructor<ClientProps>;
          Raster: ElementConstructor<RasterProps>;
          Image: ElementConstructor<ImageProps>;
      };
      desktop: {
          Box: ElementConstructor<BoxProps>;
          Text: ElementConstructor<TextProps>;
          Button: ElementConstructor<ButtonProps>;
          Input: ElementConstructor<InputProps>;
          Select: ElementConstructor<SelectProps>;
          Svg: ElementConstructor<SvgProps>;
          Link: ElementConstructor<LinkProps>;
          Code: ElementConstructor<CodeProps>;
          Markdown: ElementConstructor<MarkdownProps>;
          Client: ElementConstructor<ClientProps>;
      };
      /**
       * No `Input` or `Select`: the mobile app draws no field yet; not a limit
       * of the device, nor of the control protocol (ui_input, ui_select).
       *
       * The table grows when the app draws them.
       */
      mobile: {
          Box: ElementConstructor<BoxProps>;
          Text: ElementConstructor<TextProps>;
          Button: ElementConstructor<ButtonProps>;
          Svg: ElementConstructor<SvgProps>;
          Link: ElementConstructor<LinkProps>;
          Code: ElementConstructor<CodeProps>;
          Markdown: ElementConstructor<MarkdownProps>;
      };
      /**
       * The desktop's table without `Client`: a remote `Client`'s module, presses
       * and posts (ui_client_module, ui_client_press, ui_message) name no surface.
       *
       * They are the desktop's alone today, not a limit of the editor's webview:
       * the table gains `Client` when those asks name a surface.
       */
      vscode: {
          Box: ElementConstructor<BoxProps>;
          Text: ElementConstructor<TextProps>;
          Button: ElementConstructor<ButtonProps>;
          Input: ElementConstructor<InputProps>;
          Select: ElementConstructor<SelectProps>;
          Svg: ElementConstructor<SvgProps>;
          Link: ElementConstructor<LinkProps>;
          Code: ElementConstructor<CodeProps>;
          Markdown: ElementConstructor<MarkdownProps>;
      };
  };

  /**
   * The table `ui.resolve` answers for an argument of surface `P`.
   */

// ======== líneas 5237-5330: ImageProps y UiBlit de Image ========
  /**
   * A `$.ui.blit` argument swapping one of the caller's mounted keyed Images
   * to its next picture; every call sends it, so a stream needs no generation.
   *
   * The surface writes them with its frames, some sixty a second: byte and
   * `file` sources fold to the last per frame; every `shm` source reaches the
   * terminal (it unlinks each), and is denied while frames are not written.
   *
   * @example await $.ui.blit({ requestId: 'browser', key: 'view',
   *   source: { shm: '/tb-4', format: 'rgb', width: 1280, height: 720 } })
   */
  export type ImageBlitArgs = {
      /**
       * The site the Image is drawn in, by the `requestId` this plugin draws it
       * under.
       */
      requestId: string;
      /**
       * The Image's `key` in that drawing.
       */
      key: string;
      /**
       * The next picture (ImageSource): bytes, or a name the terminal reads.
       */
      source: ImageSource;
      /**
       * Refused unless it is the mounted Image's width in cells. Absent, that.
       */
      columns?: number;
      /**
       * Refused unless it is the mounted Image's height in cells. Absent, that.
       */
      rows?: number;
  };

  /**
   * The props of `Image`, the terminal surface's picture leaf: pixels over a
   * box of cells where the terminal can (kitty, Ghostty), the `alt` elsewhere.
   *
   * A leaf: no children, `hover` or `onPress`; the cells are text, so the
   * picture scrolls and clips as a word does. Drawn again with another `source`
   * it is replaced in place; keyed, `$.ui.blit` swaps it at the frame rate.
   *
   * @example const { bytes } = await $.fs.read('chart.png', { as: 'bytes' })
   * <Image source={{ png: bytes.toBase64() }} columns={40} rows={12} alt="p95" />
   * @example <Image key="view" source={{ shm: '/tb-7', format: 'rgb', width: 960,
   *   height: 600 }} columns={80} rows={25} alt="the page" />
   */
  export type ImageProps = {
      /**
       * The element's address within the drawing: what `$.ui.blit` names to swap.
       *
       * Unique among the Images of one tree; absent, only a redraw changes it.
       */
      key?: string;
      /**
       * The picture (ImageSource): `{ png }` or `{ rgba, width, height }` bytes,
       * or `{ file, format }` / `{ shm, format, width, height }` read here.
       */
      source: ImageSource;
      /** How many terminal columns wide, 1 to 255; the picture is scaled to fill
       * the box and the site clips what its body cannot show. */
      columns: number;
      /**
       * How many terminal rows tall, 1 to 255.
       */
      rows: number;
      /**
       * What the picture says, drawn dim in its place where the picture cannot
       * be (and read by a screen reader); required, may be a single space.
       */
      alt: string;
  };

  /**
   * The picture an `Image` shows: base64 bytes the plugin holds (at most 2 MiB
   * decoded), or the name of a file or POSIX shared-memory object it does not.
   *
   * A name is one another process on this machine wrote; the terminal, running
   * as the person, opens, reads and decodes it itself, so no pixel crosses `$`
   * and the engine never touches it. One it will not read (not a regular file,
   * under `/proc`, `/sys` or `/dev`, gone, across ssh) draws a blank box, its
   * words in the debug log; it unlinks a shared-memory object once read, so
   * each frame is a fresh one. A source equal to the last drawn sends nothing;
   * `generation` makes new content under an unchanged name a new source.
   *
   * @example { rgba: pixels.toBase64(), width: 64, height: 32 }
   * @example { file: '/dev/shm/frame-3.rgba', format: 'rgba', width: 640,
   *   height: 400 }
   * @example { shm: '/tb-view-2', format: 'rgb', width: 1280, height: 720 }
   */
  export type ImageSource = {
      /**
       * A whole PNG file, base64.

// ======== líneas 7333-7404: PaneOpenArgs: rows, columns, focus ========
  export type PaneOpenArgs = {
      /**
       * Names the pane: 1-64 of letters, digits, `_` and `-`. One pane per id:
       * opening an open id delivers the new title, never a second instance.
       *
       * Pinned at the hooks: `next(e)` passes it on; the title and focus rewrite.
       */
      id: string;
      /**
       * The pane's tab while more than one pane is open (with one, no title is
       * drawn), and the `title` its hook sees; the id when omitted.
       *
       * An unpaired surrogate half (a `.slice()` through an emoji) is drawn as
       * U+FFFD; a control character is refused.
       */
      title?: string;
      /**
       * A request, not a grant: the surface focuses (and raises) the pane only
       * while the prompt has the keys over an empty composer.
       *
       * An element of the band or a pane the person holds, text in the
       * composer, a dialog or a survey each refuse it: the pane opens without
       * the keyboard.
       */
      focus?: true;
      /**
       * While the pane holds the keyboard, the key that hands it back (Escape)
       * also closes it as the person's close does: `ui.close`, origin `person`.
       *
       * So does Escape at an idle, empty prompt once the prompt has the keys
       * again (the person typed, or `focus` was refused); over text, a turn, a
       * dialog, a footer selection, a viewed agent or a prompt mode it is theirs.
       *
       * @remarks A hook may refuse that close and keep it open. Left out, Escape
       *   returns the keys and the pane stays. Each open sets it anew, as a title.
       */
      closeOnEscape?: true;
      /**
       * While the pane is the one shown the surface holds every transient toast:
       * each other plugin's `$.ui.toast` and the engine's own, as this plugin's.
       *
       * The toast stack is not drawn, its timers waiting; the notification line
       * queues all but the engine's standing warnings, and one up as the pane opens
       * may end unseen. After, the stack draws its newest few, the line one by one.
       *
       * @remarks For a dialog the person answers and leaves, not a pane that stays.
       *   Left out, toasts show. Every open sets it; a `ui.open` hook may drop it.
       */
      holdToasts?: true;
      /**
       * The body rows the pane's content wants while seated inline above the
       * prompt: it opens that tall, up to what the layout spares, not a third.
       *
       * A request, not a grant: a size the person dragged or keyed the block
       * to wins, this session's or a kept one, and the dock ignores it. A
       * positive whole number; left out, a third. Each open sets it anew.
       */
      rows?: number;
      /**
       * The body columns the pane's content wants while docked beside a
       * fullscreen transcript: the dock opens that wide, floor to ceiling.
       *
       * A request, not a grant: a width the person dragged or keyed the dock
       * to wins, this session's or a kept one, and the inline block ignores
       * it. A positive whole number; left out, the share. Each open sets it anew.
       *
       * @example
       * await $.ui.open({ id: "browser", focus: true, rows: 24, columns: 100 })
       */
      columns?: number;
  };


// ======== líneas 9147-9216: RasterProps y RasterBlitArgs (límites de columnas y filas, 1024 pares) ========
  /**
   * A `$.ui.blit` argument repainting one of the caller's mounted Rasters.
   *
   * `columns` and `rows`, when given, must be the mounted size (a resize is a
   * redraw, `$.ui.invalidate("ui.render")`, not a blit).
   */
  export type RasterBlitArgs = {
      /**
       * The site the Raster is drawn in, by the `requestId` this plugin draws
       * it under: one of its panes' ids, a tool row's `tool_use_id`, the band's.
       */
      requestId: string;
      /**
       * The Raster's `key` in that drawing.
       */
      key: string;
      /**
       * The new cells, encoded as the element's `cells` are (RasterProps), for
       * the mounted `columns * rows`.
       */
      cells: string;
      /**
       * The width the cells are laid out for; refused unless it is the mounted
       * Raster's. Absent, the mounted width.
       */
      columns?: number;
      /**
       * The height the cells are laid out for; refused unless it is the mounted
       * Raster's. Absent, the mounted height.
       */
      rows?: number;
  };

  /**
   * The props of `Raster`, the terminal surface's cell-grid leaf: a fixed box
   * of cells, each a glyph, a foreground and a background, packed in `cells`.
   *
   * A leaf: no children, `hover` or `onPress` yet; repainted in place by
   * `$.ui.blit`. Terminal only for now (elsewhere a fragment); its palette
   * paints 1024 distinct color pairs at once and the rest as their nearest.
   */
  export type RasterProps = {
      /**
       * The element's address within the drawing: what `$.ui.blit` names to
       * repaint it, unique among the Rasters of one tree.
       */
      key: string;
      /**
       * How many terminal columns wide, 1 to 512; the site clips what its body
       * cannot show.
       */
      columns: number;
      /**
       * How many terminal rows tall, 1 to 256.
       */
      rows: number;
      /**
       * Every cell, row-major: standard padded base64 of `columns * rows`
       * little-endian u32 triplets `[codePoint, foreground, background]`.
       *
       * A code point is one printable width-1 BMP character (blocks, box drawing,
       * braille too), or the tree is refused naming the cell's index; a color is
       * `0x00RRGGBB`, or `0x01000000` (bit 24 alone) for the terminal's default.
       *
       * @example const words = Uint32Array.of(0x2588, 0xff8800, 0x01000000)
       * const cells = new Uint8Array(words.buffer).toBase64() // one orange cell
       */
      cells: string;
  };


// ======== líneas 10180-10246: AbovePrompt: maxRows, bodyColumns, scroll ========
      /**
       * The band directly above the prompt input, where the surveys draw; of its
       * own the engine draws a `[-]` beside the tree, an `n more` row under it.
       *
       * A hook draws a tree, or passes; one instance. The person collapses it
       * (ctrl+x ctrl+a, `[-]`) or focuses it (a click, ctrl+x tab): an Input
       * types, a Button arms the hotkeys, a tree taller than it scrolls.
       *
       * Raised on the terminal and desktop surfaces only.
       */
      AbovePrompt: {
          /**
           * True while a survey holds the band; a hook yields to it. Read-only.
           */
          hasSurvey: boolean;
          /**
           * True while a model turn is running. Read-only.
           */
          isWorking: boolean;
          /**
           * Rows the band may take: in fullscreen, what the bottom slot has left
           * above the prompt; otherwise the terminal's height. Read-only.
           *
           * That slot is capped at half the terminal's rows, the prompt's included.
           * A tree of at most `maxRows` rows shows whole; a taller one scrolls in a
           * window of `scroll.bodyRows`.
           *
           * @remarks A bare digit arms only the hotkeys of the Buttons wholly inside
           *   that window, never one scrolled out of view.
           */
          maxRows: number;
          /**
           * Cells the band's tree is laid out in, none under a mark of the engine's:
           * its column's width less the engine's five at the right end. Read-only.
           *
           * The column is the terminal, or the transcript's beside a docked `Pane`;
           * the five hold the `[-]`. A wider tree wraps or truncates as its Text
           * props say; size a table to it rather than to `viewport.columns`.
           */
          bodyColumns: number;
          /**
           * The band's window over a tree taller than `maxRows`: engine-owned,
           * moved by the wheel, and by the person's keys while the band is focused.
           *
           * `bodyRows` is `maxRows` less the `n more` row. Read-only.
           */
          scroll: SiteScroll;
          /**
           * Which transcript is on screen above the band: the main conversation's
           * (no `agentId`) or one agent's, opened from the tasks list.
           *
           * The same band under either; a switch re-runs the hook with the new
           * view. Read-only: a rewrite carries it on as received; one that changes
           * or drops it is refused, the hook that passed it failing.
           */
          view: SiteView;
      };
      /**
       * The framed region a plugin opened with `$.ui.open({ id })`: one instance
       * per id (`requestId`), its body the hook's tree, one shown, the rest tabs.
       *
       * Placed by the surface (docked in fullscreen, else above the prompt) and
       * keyed by the person (ctrl+x tab, Esc), who closes it from the engine's mark
       * or ctrl+x x: `ui.close` with origin `person`, which a hook may refuse.
       *
       * Raised on every surface.
       */

// ======== líneas 10247-10352: Pane (dock o inline) y RenderViewport (isFullscreen) ========
      Pane: {
          /**
           * Its tab's label while more than one pane is open (with one, the engine
           * draws no title): the `title` it was opened with, or its id.
           *
           * A click on a tab, or Tab onto it and Enter, shows that pane. Read-only
           * here; another `$.ui.open` (or a hook on `ui.open`) retitles.
           */
          title: string;
          /**
           * True while the person has given the pane the keyboard: Tab walks its
           * elements, a Button's `hotkey` presses it, the arrows scroll. Read-only.
           */
          isFocused: boolean;
          /**
           * Cells across the body, inside the frame, none under a mark of the
           * engine's: the close mark sits on a row of the frame's own. Read-only.
           */
          bodyColumns: number;
          /**
           * Where the surface seated the pane: `dock` beside the transcript (the
           * terminal in fullscreen from 110 columns), or `inline` above the prompt.
           *
           * Read-only: a rewrite carries it on as received; one that changes or
           * drops it is refused, the hook that passed it failing.
           */
          placement: 'dock' | 'inline';
          /**
           * The body's window over the tree: engine-owned, moved by the person's
           * keys while the pane is focused. Read-only.
           *
           * `bodyRows` is the room's rows, never the rows showing: the most the frame
           * may take less the engine's (an inline border's two, the tab row while one
           * shows, a dock's row for the close mark). Inline the frame fits the tree.
           */
          scroll: SiteScroll;
          /**
           * Which transcript is on screen beside the pane: the main conversation's
           * (no `agentId`) or one agent's, opened from the tasks list.
           *
           * The pane stays open across a switch, one instance re-rendered for the
           * view, so a hook draws for the agent in view. Read-only: a rewrite carries
           * it on as received; one that changes or drops it is refused.
           */
          view: SiteView;
      };
  };

  /**
   * What a `ui.render` hook returns and what `next(e)` resolves to: a
   * RenderElement tree, the same for every component.
   */
  export type RenderResultOf = {
      [C in RenderComponent]: RenderElement;
  };

  /**
   * Where a render event's component is drawn: `terminal` is Ink, which draws
   * the hook's whole tree; the rest are remote surfaces drawing it themselves.
   *
   * `desktop` is Claude Code Desktop, `mobile` the Claude mobile app, `vscode`
   * Claude Code for VS Code. A remote surface asks over the wire (ui_render),
   * draws with the props the hook handed core, and draws the tree where it has
   * a slot for it.
   *
   * Each surface's ask is its own evaluation, since a tree may hold an element
   * only some surfaces draw (Svg, Client).
   */
  export type RenderSurface = 'terminal' | 'desktop' | 'mobile' | 'vscode';

  /**
   * The size of what a surface draws into, in character cells of the
   * surface's monospace metric, and whether its layout docks a pane.
   *
   * On the terminal, the conversation's columns and screen rows; on a remote
   * surface, the pane's width and height over the advance and line height of
   * its code font. Cell-based until the first element lays out in pixels.
   */
  export type RenderViewport = {
      /**
       * Cells across. A tree wider than this wraps or truncates, as its Text
       * props say.
       */
      columns: number;
      /**
       * Cells down the whole surface, not the room left for this component.
       *
       * Informational: a change of height alone re-draws nothing and keys no
       * new evaluation, so a hook reads it as of the last width or props change.
       */
      rows: number;
      /**
       * Whether this surface docks a pane beside the transcript, so a pane a
       * plugin opens unasked is a sidebar, not a takeover; absent is unknown.
       *
       * What `command.run`'s `presentation.isFullscreen` says. The terminal always
       * says: `true` fullscreen, `false` on the main screen, fixed per session; a
       * remote surface once its client reports it with the size, absent before.
       *
       * @remarks A remote surface that reports it places panes (`$.ui.open` is
       *   placed there); the mobile app reports `false`. A change re-draws.
       * @example if (e.viewport?.isFullscreen === true) void $.ui.open({ id })
       */
      isFullscreen?: boolean;
  };


// ======== líneas 12203-12231: SvgProps ========
  export type SvgProps = {
      /**
       * The SVG document, `<svg ...>...</svg>`, at most 131072 characters.
       */
      source: string;
      /**
       * What the drawing says, for a reader that cannot see it; required, since
       * a surface without the element draws nothing else of it.
       */
      alt: string;
      /**
       * CSS pixels; absent, the box takes the markup's own width up to the slot.
       */
      width?: number;
      /**
       * CSS pixels; absent, the markup's own height at the drawn width.
       */
      height?: number;
      /**
       * `true` draws the SVG in a script-less sandboxed frame so hover, CSS
       * `:hover`, SMIL animation and `<title>` tooltips work; absent, an image.
       *
       * It never enables script or event-handler attributes (the frame has no
       * allow-scripts and the scrub strips them); presses that other plugins
       * should observe go on an enclosing element.
       */
      isInteractive?: boolean;
  };


// ======== líneas 3465-3490: $.process.run ========
       * Commands on the host, run as the user the session runs as. CLI only.
       *
       * Local execution, not a network path: what a command of its own reaches
       * is its own, as for the Bash tool and a settings `command` hook.
       */
      process: {
          /**
           * Runs a command on the host by its argument vector (no shell) and
           * resolves `{ exitCode, stdout, stderr }` once it exits, any exit code.
           *
           * One shot: the whole output is read, so a background process left
           * writing holds the call until the timeout. Rejects when the command
           * cannot start or is still running then. Git runs with repo hooks off.
           *
           * @param argv the command and its arguments, `argv[0]` the executable
           * @param init `{ cwd, env, stdin, timeoutMs }` (cwd the session's by
           *             default; timeout 30 s by default, ten minutes at most)
           * @returns `{ exitCode, stdout, stderr }`, each stream's first 4194304
           *          bytes (`isStdoutTruncated`, `isStderrTruncated` say when cut)
           * @example
           * const { exitCode, stdout } = await $.process.run(["git", "status"])
           */
          run: (argv: readonly string[], init?: ProcessRunInit) => Promise<ProcessRunResult>;
          /**
           * Starts a command on the host by its argument vector (no shell) and
           * streams what it writes, piece by piece, then how it ended.
