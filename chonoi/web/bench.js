"use strict";
(function () {
  const params = new URLSearchParams(location.search);
  if (params.get("bench") !== "1") return;

  const warmupSec = parseFloat(params.get("warmup") || "3");
  const durationSec = parseFloat(params.get("duration") || "30");
  const warmupMs = warmupSec * 1000;
  const durationMs = durationSec * 1000;

  let state = "waiting_first_frame";
  let firstFrameTime = 0;
  let lastTime = 0;
  let totalDt = 0;
  const frameMs = [];
  let firstFrameRequest;

  window.BENCH = function onFrame(now) {
    if (state === "done") return;

    if (state === "waiting_first_frame") {
      state = "warming_up";
      firstFrameTime = now;
      firstFrameRequest = fetch("/bench/first-frame", { method: "POST" });
      firstFrameRequest.catch(() => {});
      return;
    }

    if (state === "warming_up") {
      if (now - firstFrameTime >= warmupMs) {
        state = "measuring";
        lastTime = now;
      }
      return;
    }

    if (state === "measuring") {
      const dt = now - lastTime;
      lastTime = now;
      frameMs.push(dt);
      totalDt += dt;

      if (totalDt >= durationMs) {
        state = "done";
        firstFrameRequest.then(() => fetch("/bench/result", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ frame_ms: frameMs }),
        })).catch(() => {});
        return;
      }
    }
  };
})();
