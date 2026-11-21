"use strict";
/*
 * Lớp SÁNG TẠO của nhóm (A âm thanh · C lời thoại · H sổ tay Út Sen).
 * - Chỉ chạy khi trang mở với ?creative=1. Không có cờ thì file này không được nạp (xem index.html).
 * - CHỈ ĐỌC snapshot/events từ index.html, không gửi gì lên máy chủ, không đụng luật, headless không biết tới file này.
 * - Math.random ở đây chỉ để chọn câu thoại/âm sắc; không đi vào sim (sim dùng Streams).
 * - Phím M = bật/tắt tiếng. Mặc định nhạc nền nhỏ; trình duyệt chỉ cho phát âm thanh sau khi người chơi bấm phím.
 * Chi tiết: docs/creative-ideas.md
 */
(function () {
  const LINES = {
    gather:      ["Hái được rồi nè!", "Bông súng tươi dữ!", "Điên điển vàng ươm!"],
    fish_caught: ["Dính cá rồi!", "Cá lóc nè, béo dữ!", "Bắt được con cá linh!"],
    hold_full:   ["Giỏ đầy rồi, về bến thôi!", "Hết chỗ chứa nè!"],
    choke:       ["Hụt hơi rồi nè!", "Ngộp quá trời ơi!"],
    faint:       ["Trời ơi, xỉu rồi...", "Hết hơi rồi!"],
    node_regrown: ["Bông súng mọc lại nè."],
    gather_end:  ["Xong buổi sáng, về bến!", "Anh Jack: Dừa Bến Tre nè, ngọt dữ nha!"],
    cook_started: ["Bắt đầu nấu nè!", "Lửa đượm rồi!"],
    dish_ready:  ["Món chín rồi, bưng đi!", "Thơm nức mũi luôn!"],
    served:      ["Mời bà con dùng!", "Nóng hổi nè!"],
    paid:        ["Cảm ơn bà con!", "Chị Thiên An: Ngon nha, tui boa thêm!"],
    customer_arrived: ["Khách tới kìa!", "Anh Jack: Cho tui món gì ngon ngon nha!", "Chị Thiên An: Ổng nói hoài, cho tui miếng cá lẹ giùm."],
    customer_left: ["Khách bỏ đi mất tiêu...", "Chị Thiên An: Chờ lâu dữ vậy!"],
    no_dish:     ["Hết món rồi bà con ơi!"],
    quan_end:    ["Dọn quán thôi, mai bán tiếp!"],
  };
  const pick = (a) => a[Math.floor(Math.random() * a.length)];
  const enabled = /[?&]creative=1(&|$)/.test(location.search);
  if (!enabled) return;

  // ---------------- A: âm thanh Web Audio (không cần file) ----------------
  let ac = null, master = null, muted = false, ambient = null;
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* bỏ qua */ } },
  };
  muted = store.get("creative.muted", false);

  function ensureAudio() {
    if (ac) { if (ac.state === "suspended") ac.resume(); return ac; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ac = new AC();
    master = ac.createGain(); master.gain.value = muted ? 0 : 0.5; master.connect(ac.destination);
    startAmbient();
    return ac;
  }
  function tone(freq, dur, type, vol, slideTo, delay) {
    if (!ac || muted) return;
    const t0 = ac.currentTime + (delay || 0);
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type || "sine"; o.frequency.setValueAtTime(freq, t0);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t0 + dur);
    g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(vol || 0.3, t0 + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(master); o.start(t0); o.stop(t0 + dur + 0.02);
  }
  function noiseBurst(dur, vol, cutoff) {
    if (!ac || muted) return;
    const n = Math.floor(ac.sampleRate * dur), buf = ac.createBuffer(1, n, ac.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
    const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
    s.buffer = buf; f.type = "lowpass"; f.frequency.value = cutoff || 800; g.gain.value = vol || 0.3;
    s.connect(f); f.connect(g); g.connect(master); s.start();
  }
  function startAmbient() {  // tiếng nước rì rào rất nhỏ: nhiễu lọc thấp + sóng chậm
    const n = ac.sampleRate * 2, buf = ac.createBuffer(1, n, ac.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain(), lfo = ac.createOscillator(), lg = ac.createGain();
    s.buffer = buf; s.loop = true; f.type = "lowpass"; f.frequency.value = 420; g.gain.value = 0.05;
    lfo.frequency.value = 0.15; lg.gain.value = 0.025; lfo.connect(lg); lg.connect(g.gain);
    s.connect(f); f.connect(g); g.connect(master); s.start(); lfo.start();
    ambient = g;
  }
  const SFX = {
    gather:      () => { tone(520, 0.08, "triangle", 0.25); tone(780, 0.1, "triangle", 0.2, null, 0.07); },
    fish_caught: () => { tone(300, 0.18, "sine", 0.3, 900); noiseBurst(0.12, 0.15, 1500); },
    hold_full:   () => { tone(220, 0.12, "square", 0.15); tone(220, 0.12, "square", 0.15, null, 0.16); },
    choke:       () => tone(160, 0.2, "sawtooth", 0.15, 110),
    faint:       () => tone(300, 0.7, "sawtooth", 0.2, 70),
    node_regrown: () => tone(660, 0.08, "sine", 0.1),
    gather_end:  () => [523, 659, 784].forEach((f, i) => tone(f, 0.2, "triangle", 0.25, null, i * 0.12)),
    cook_started: () => noiseBurst(0.35, 0.2, 2500),
    dish_ready:  () => { tone(1046, 0.25, "sine", 0.3); tone(1568, 0.35, "sine", 0.22, null, 0.08); },
    served:      () => tone(440, 0.1, "triangle", 0.25),
    paid:        () => { tone(988, 0.08, "square", 0.15); tone(1318, 0.18, "square", 0.15, null, 0.08); },
    customer_arrived: () => { tone(700, 0.1, "sine", 0.2); tone(880, 0.12, "sine", 0.2, null, 0.1); },
    customer_left: () => tone(330, 0.3, "sawtooth", 0.15, 160),
    no_dish:     () => tone(200, 0.15, "square", 0.15),
    quan_end:    () => [784, 659, 523].forEach((f, i) => tone(f, 0.22, "triangle", 0.25, null, i * 0.14)),
  };

  addEventListener("keydown", (e) => {
    ensureAudio();  // trình duyệt chỉ mở âm thanh sau thao tác của người chơi
    if (e.key && e.key.toLowerCase() === "m" && !e.repeat) {
      muted = !muted; store.set("creative.muted", muted);
      if (master) master.gain.value = muted ? 0 : 0.5;
      toast(muted ? "Tắt tiếng (M để bật)" : "Bật tiếng (M để tắt)", "sys");
    }
  });
  addEventListener("pointerdown", ensureAudio);

  // ---------------- C: lời thoại (toast) ----------------
  const toasts = [];  // {text, born, kind}
  function toast(text, kind) {
    toasts.push({ text, born: performance.now(), kind: kind || "say" });
    if (toasts.length > 4) toasts.shift();
  }

  // ---------------- H: sổ tay Út Sen ----------------
  const run = { gather: 0, fish: 0, served: 0, paid: 0, left: 0, faint: 0 };
  let diary = store.get("creative.diary", []);
  let lastEntry = "";
  function resetRun() { for (const k in run) run[k] = 0; lastEntry = ""; }
  function writeDiary(mode, snap) {
    const d = new Date(), day = d.getDate() + "/" + (d.getMonth() + 1);
    let s;
    if (mode === "gather") {
      s = `Hôm nay (${day}) Út Sen hái ${run.gather} bó rau, bắt ${run.fish} con cá` + (run.faint ? `, xỉu ${run.faint} lần` : "") +
        ". Anh Jack Bến Tre ghé cho thêm mấy trái dừa xiêm.";
    } else {
      const earned = (snap && snap.earned) !== undefined ? snap.earned : run.paid;
      s = `Tối ${day}, quán bán ${run.served} phần, thu ${earned}k` + (run.left ? `, ${run.left} khách bỏ về` : "") +
        ". Chị Thiên An khen món ngon, hẹn mai ghé nữa.";
    }
    lastEntry = s; diary.push(s); diary = diary.slice(-20); store.set("creative.diary", diary);
  }

  // ---------------- nhận snapshot từ index.html ----------------
  const seen = new Set(); let lastTick = -1, wroteFor = null;
  function onSnap(snap) {
    if (!snap) return;
    if (typeof snap.tick === "number" && snap.tick < lastTick) { seen.clear(); resetRun(); wroteFor = null; }  // R = chơi lại
    if (typeof snap.tick === "number") lastTick = snap.tick;
    (snap.events || []).forEach((e) => {
      const key = e.tick + "|" + e.name + "|" + JSON.stringify(e.data);
      if (seen.has(key)) return;
      seen.add(key); if (seen.size > 200) seen.delete(seen.values().next().value);
      if (e.name === "gather") run.gather++;
      else if (e.name === "fish_caught") run.fish++;
      else if (e.name === "served") run.served++;
      else if (e.name === "paid") run.paid += (e.data && e.data.amount) || 0;
      else if (e.name === "customer_left") run.left++;
      else if (e.name === "faint") run.faint++;
      if (SFX[e.name]) SFX[e.name]();
      if (LINES[e.name]) toast(pick(LINES[e.name]), e.name);
    });
    if (snap.finished && wroteFor !== snap.mode + snap.tick) { wroteFor = snap.mode + snap.tick; writeDiary(snap.mode, snap); }
  }

  // ---------------- vẽ lớp sáng tạo (đè lên HUD của index.html) ----------------
  function draw(ctx, w, h, snap) {
    const now = performance.now();
    while (toasts.length && now - toasts[0].born > 3500) toasts.shift();
    ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.font = "16px system-ui, sans-serif";
    toasts.forEach((t, i) => {
      const age = (now - t.born) / 3500, a = Math.max(0, Math.min(1, (1 - age) * 3));
      const y = h * 0.28 + i * 30;
      ctx.globalAlpha = a; const tw = ctx.measureText(t.text).width + 24;
      ctx.fillStyle = t.kind === "sys" ? "rgba(30,30,30,.7)" : "rgba(255,244,214,.92)"; ctx.fillRect(w / 2 - tw / 2, y - 14, tw, 28);
      ctx.fillStyle = t.kind === "sys" ? "#ddd" : "#4a2f12"; ctx.fillText(t.text, w / 2, y);
    });
    ctx.globalAlpha = 1;
    if (snap && snap.finished && lastEntry) {  // sổ tay hiện ở màn kết, dưới bảng "kết thúc"
      const bw = Math.min(w - 40, 520), x = (w - bw) / 2, y = h / 2 + 70;
      ctx.fillStyle = "rgba(255,244,214,.95)"; ctx.fillRect(x, y, bw, 78);
      ctx.fillStyle = "#6b4a2b"; ctx.font = "12px system-ui, sans-serif"; ctx.fillText("Sổ tay Út Sen", w / 2, y + 12);
      ctx.fillStyle = "#4a2f12"; ctx.font = "italic 14px system-ui, sans-serif"; ctx.textAlign = "left";
      wrap(ctx, lastEntry, x + 12, y + 32, bw - 24, 18);
    }
    ctx.fillStyle = "rgba(232,238,242,.5)"; ctx.font = "11px system-ui, sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillText("♪ M tắt/bật tiếng · sáng tạo bật", 10, h - 14);
    ctx.restore();
  }
  function wrap(ctx, s, x, y, maxW, lh) {
    let line = "";
    s.split(" ").forEach((word) => {
      const t = line ? line + " " + word : word;
      if (ctx.measureText(t).width > maxW && line) { ctx.fillText(line, x, y); y += lh; line = word; } else line = t;
    });
    if (line) ctx.fillText(line, x, y);
  }

  window.CREATIVE = { onSnap, draw };
})();
