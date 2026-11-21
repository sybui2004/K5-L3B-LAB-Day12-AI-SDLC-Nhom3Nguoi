"use strict";
/*
 * Các màn hình của mode day: menu, DayIntro, EveningIntro, DayResult, Shop, Summary, pause.
 * CHỈ ĐỌC snapshot và gửi lệnh qua API do index.html truyền vào; không chứa luật, headless không biết tới file này.
 */
(function () {
  const root = document.getElementById("screen");
  const INTRO_MS = { day_intro: 4000, evening_intro: 6000 };
  const KEY_GUARD_MS = 350;   // phím đang bấm dở ở pha trước không được bỏ qua màn vừa mở
  const UPGRADE = {
    oxygen: { name: "Bình oxy", key: "1", value: (u) => `Lặn được ${u.oxygen_max_s} giây` },
    hp: { name: "Áo phao", key: "2", value: (u) => `${u.hp_max} Máu mỗi ngày` },
  };
  const FISH = '<svg viewBox="0 0 64 36" aria-hidden="true"><path fill="currentColor" d="M2 18C12 5 30 3 44 13l17-10-5 15 5 15-17-10C30 33 12 31 2 18z"/><circle cx="14" cy="15" r="2.6" fill="#132B2E"/></svg>';
  const FLOWER = '<svg viewBox="0 0 48 48" aria-hidden="true"><g fill="currentColor"><ellipse cx="24" cy="11" rx="7" ry="10"/><ellipse cx="24" cy="37" rx="7" ry="10"/><ellipse cx="11" cy="24" rx="10" ry="7"/><ellipse cx="37" cy="24" rx="10" ry="7"/></g><circle cx="24" cy="24" r="5.5" fill="#FAF6E3"/></svg>';
  const LEAF = '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="currentColor" d="M6 42C4 20 18 6 43 5c1 24-13 39-37 37z"/><path d="M8 40 34 15" stroke="#132B2E" stroke-width="2" fill="none"/></svg>';
  const SHAPE = { ca_loc: FISH, ca_linh: FISH, ca_keo: FISH, bong_sung: FLOWER, bong_dien_dien: FLOWER, keo_neo: LEAF };

  let api = null, snap = null, quit = false, view = null, sig = "", openedAt = 0, autoTimer = null, timerEl = null;

  function h(tag, cls, ...kids) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    for (const k of kids) if (k !== null && k !== undefined) n.append(k);
    return n;
  }
  function button(label, onClick, cls) {
    const b = h("button", cls || "", label);
    b.type = "button";
    b.addEventListener("click", onClick);
    return b;
  }
  function pole(items) {
    const list = h("ul", "beo");
    items.forEach((it, i) => {
      const art = h("span", "beo-art");
      art.innerHTML = SHAPE[it.kind] || LEAF;    // chỉ chèn hằng SVG ở trên
      art.style.color = api.kindColor(it.kind);
      const li = h("li", "beo-item", art, h("span", "beo-name", it.label));
      li.style.setProperty("--i", i);
      list.append(li);
    });
    return list;
  }
  function stats(rows) {
    const dl = h("dl", "stats");
    for (const [k, v] of rows) dl.append(h("div", "stat", h("dt", "", k), h("dd", "", String(v))));
    return dl;
  }
  function sheet(copy, side) {
    return h("div", "sheet" + (side ? "" : " sheet-solo"), h("section", "copy", ...copy), side || null);
  }
  const advance = (gate) => api.post("/advance", { gate });
  const toMenu = () => { quit = false; api.post("/restart", {}); };
  function fmtDelta(v) { return (v > 0 ? "+" : "") + Number(v || 0).toFixed(1); }
  function allKinds(s) {
    const kinds = new Set();
    Object.values(s.menu || {}).forEach((d) => Object.keys(d.recipe || {}).forEach((k) => kinds.add(k)));
    return [...kinds].sort();
  }
  function cookable(s) {
    const plan = (s.day_plan && s.day_plan.dishes) || {}, stock = api.stockCounts(s.stock);
    return Object.keys(plan).map((d) => {
      const recipe = (s.menu[d] || {}).recipe || {};
      const most = Math.min(...Object.entries(recipe).map(([k, n]) => Math.floor((stock[k] || 0) / n)));
      return [d, Math.min(plan[d], Number.isFinite(most) ? most : 0)];
    }).filter(([, n]) => n > 0);
  }
  function bestDish(tally) {
    const rows = Object.entries((tally && tally.dishes) || {}).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
    return rows.length ? api.dishName(rows[0][0]) : "Chưa bán được món nào";
  }

  // ---------- từng màn ----------
  const VIEWS = {
    menu(s) {
      const items = allKinds(s).map((k) => ({ kind: k, label: api.kindName(k) }));
      return sheet([
        h("h1", "title", "Quán Ăn Chợ Nổi"),
        h("p", "lede", "Sáng lặn sông hái đồ, tối mở quán trên ghe."),
        h("p", "note", "Nhấn C để bật hoặc tắt tương phản cao."),
        h("div", "actions", button("Chơi", () => advance("menu"), "primary"), button("Thoát", () => { quit = true; render(true); })),
      ], pole(items));
    },
    quit() {
      return sheet([
        h("h1", "title", "Đã rời chợ"),
        h("p", "lede", "Bạn có thể đóng tab này."),
        h("div", "actions", button("Về menu", () => { quit = false; render(true); }, "primary")),
      ]);
    },
    day_intro(s) {
      const plan = s.day_plan || { dishes: {}, ingredients: {} };
      const dishes = h("ul", "plain");
      for (const [d, n] of Object.entries(plan.dishes)) dishes.append(h("li", "", `${n} phần ${api.dishName(d)}`));
      const items = Object.entries(plan.ingredients).map(([k, n]) => ({ kind: k, label: `${api.kindName(k)} ×${n}` }));
      return sheet([
        h("h1", "title", `Ngày ${s.day}`),
        h("p", "lede", "Má Tư dặn hôm nay nấu:"),
        dishes,
        h("div", "actions", button("Xuống sông", () => advance("day_intro"), "primary")),
        h("div", "fuse fuse-day"),
      ], pole(items));
    },
    evening_intro(s) {
      const stock = Object.entries(api.stockCounts(s.stock));
      const can = cookable(s);
      const list = h("ul", "plain");
      for (const [d, n] of can) list.append(h("li", "", `${n} phần ${api.dishName(d)}`));
      return sheet([
        h("h1", "title", "Tối nay mở quán"),
        h("p", "lede", can.length ? "Kho đủ để nấu:" : "Kho chưa đủ nấu món nào trong kế hoạch. Tối nay quán sẽ vắng khách."),
        can.length ? list : null,
        h("div", "actions", button("Mở quán", () => advance("evening_intro"), "primary")),
        h("div", "fuse fuse-evening"),
      ], stock.length ? pole(stock.map(([k, n]) => ({ kind: k, label: `${api.kindName(k)} ×${n}` }))) : null);
    },
    day_result(s) {
      const r = s.day_result || {};
      return sheet([
        h("h1", "title", `Hết ca ngày ${s.day}`),
        stats([
          ["Khách đã phục vụ", r.served ?? 0], ["Khách bỏ đi", r.left ?? 0], ["Tiền ca", `${r.money ?? 0}k`],
          ["Tiền boa", `${r.tips ?? 0}k`], ["Uy tín", fmtDelta(r.reputation_delta)],
          ["Món bán chạy", r.best_dish ? api.dishName(r.best_dish) : "Chưa bán được món nào"],
        ]),
        h("div", "actions", button("Ra chợ mua đồ", () => advance("day_result"), "primary")),
      ]);
    },
    shop(s) {
      const table = s.shop_table || {}, up = s.upgrades || {};
      const rows = h("div", "shop");
      for (const kind of Object.keys(UPGRADE)) {
        const info = UPGRADE[kind], levels = table[kind] || [], level = up[kind] || 0, next = levels[level];
        const dots = h("span", "dots");
        dots.setAttribute("aria-label", `Cấp ${level} trên ${levels.length}`);
        levels.forEach((_, i) => dots.append(h("i", i < level ? "on" : "")));
        let action;
        if (!next) { action = h("span", "maxed", "Đã tối đa"); }
        else if (next.price > s.money) { action = button(`Thiếu ${next.price - s.money}k`, () => {}); action.disabled = true; }
        else { action = button(`Mua ${next.price}k`, () => api.send({ buy: kind }), "primary"); }
        rows.append(h("div", "shop-row",
          h("div", "shop-name", h("strong", "", `${info.key}. ${info.name}`), dots),
          h("div", "shop-next", next ? info.value(next) : info.value(levels[levels.length - 1] || {})),
          action));
      }
      timerEl = h("span", "timer", "");
      return sheet([
        h("h1", "title", "Chợ cuối ngày"),
        h("p", "wallet", `Trong ví ${s.money}k`, timerEl),
        rows,
        h("p", "note", "Đồ mua hôm nay dùng từ ngày mai."),
        h("div", "actions", button("Rời chợ", () => api.pulse("shop_done"), "primary")),
      ]);
    },
    summary(s) {
      const t = s.tally || {};
      return sheet([
        h("h1", "title", `${s.days} ngày trên sông`),
        stats([
          ["Tổng tiền kiếm được", `${s.earned}k`], ["Điểm", s.score], ["Uy tín", Number(s.reputation).toFixed(1)],
          ["Khách đã phục vụ", t.served ?? 0], ["Khách bỏ đi", t.left ?? 0], ["Món bán chạy", bestDish(t)],
        ]),
        h("div", "actions", button("Về menu", toMenu, "primary")),
      ]);
    },
    pause(s) {
      return sheet([
        h("h1", "title", "Đang tạm dừng"),
        h("p", "lede", "Đồng hồ và mọi bộ đếm đều đứng yên."),
        h("p", "note", "Nhấn C để bật hoặc tắt tương phản cao."),
        h("div", "actions", button("Tiếp tục", () => api.pulse("pause"), "primary"),
          button(s.mode === "day" ? "Về menu" : "Chơi lại", toMenu)),
      ]);
    },
  };

  function viewOf(s) {
    if (quit && s.gate === "menu") return "quit";
    if (s.gate) return s.gate;
    if (s.state === "paused") return "pause";
    if (s.mode === "day" && s.phase === "shop" && !s.finished) return "shop";
    return null;
  }
  function signature(v, s) {
    if (v === "shop") return `shop|${s.day}|${s.money}|${JSON.stringify(s.upgrades)}`;
    return `${v}|${s.day}|${s.days_completed}`;
  }
  function render(force) {
    if (!snap) return;
    const v = viewOf(snap), next = v ? signature(v, snap) : "";
    if (v === "shop" && timerEl) timerEl.textContent = `Chợ đóng sau ${Math.ceil(snap.time_left_ticks / 60)} giây`;
    if (!force && next === sig) return;
    const changedView = v !== view;
    sig = next;
    view = v;
    if (changedView) {
      clearTimeout(autoTimer);
      openedAt = performance.now();
      if (v) api.clearKeys();
      if (INTRO_MS[v]) autoTimer = setTimeout(() => advance(v), INTRO_MS[v]);
    }
    root.replaceChildren();
    timerEl = null;
    root.hidden = !v;
    root.className = v ? `screen screen-${v}` : "screen";
    if (v) {
      root.append(VIEWS[v](snap));
      if (v === "shop") timerEl.textContent = `Chợ đóng sau ${Math.ceil(snap.time_left_ticks / 60)} giây`;
    }
  }

  // Trả về true nếu màn đang mở nhận phím (khi đó game không nhận phím này).
  function handleKey(k, e) {
    if (!view) return false;
    const onButton = document.activeElement && document.activeElement.tagName === "BUTTON" && root.contains(document.activeElement);
    if ((k === "enter" || k === " ") && onButton) return true;   // để trình duyệt bấm nút đang focus
    if (k !== "tab") e.preventDefault();
    if (e.repeat || performance.now() - openedAt < KEY_GUARD_MS) return true;
    const pauseKey = k === "escape" || k === "p";
    if (view === "pause") { if (pauseKey || k === "enter") api.pulse("pause"); }
    else if (view === "menu") { if (k === "enter") advance("menu"); }
    else if (view === "quit") { if (k === "enter") { quit = false; render(true); } }
    else if (view === "summary") { if (k === "enter") toMenu(); }
    else if (view === "shop") {
      if (pauseKey) api.pulse("pause");
      else if (k === "enter") api.pulse("shop_done");
      else for (const kind of Object.keys(UPGRADE)) if (k === UPGRADE[kind].key) api.send({ buy: kind });
    } else if (k !== "tab" && k.length && !["shift", "control", "alt", "meta"].includes(k)) {
      advance(view);    // DayIntro, EveningIntro, DayResult: phím bất kỳ
    }
    return true;
  }

  window.SCREENS = {
    init(a) { api = a; },
    sync(s) { snap = s; render(false); },
    active: () => view !== null,
    refresh: () => render(true),
    handleKey,
  };
})();
