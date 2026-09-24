/** Capture interviewer audio: meeting/tab/system first, then loopback device, then mic. */

const LOOPBACK_HINTS = [
  "blackhole",
  "cable output",
  "voicemeeter",
  "vb-audio",
  "loopback",
  "soundflower",
  "stereo mix",
  "what u hear",
  "wave out mix",
];

function _rmsFromAnalyser(analyser, buf) {
  analyser.getByteTimeDomainData(buf);
  let sum = 0;
  for (let i = 0; i < buf.length; i += 1) {
    const v = (buf[i] - 128) / 128;
    sum += v * v;
  }
  return Math.sqrt(sum / buf.length);
}

function isLoopbackLabel(label) {
  const n = String(label || "").toLowerCase();
  return LOOPBACK_HINTS.some((h) => n.includes(h));
}

function encodeWavPcm(floatChunks, sampleRate) {
  let length = 0;
  for (const c of floatChunks) length += c.length;
  if (!length) return null;
  const samples = new Int16Array(length);
  let o = 0;
  for (const c of floatChunks) {
    for (let i = 0; i < c.length; i += 1) {
      let s = c[i];
      if (s > 1) s = 1;
      else if (s < -1) s = -1;
      samples[o++] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
  }
  const bytes = samples.byteLength;
  const buf = new ArrayBuffer(44 + bytes);
  const view = new DataView(buf);
  const ascii = (off, s) => {
    for (let i = 0; i < s.length; i += 1) view.setUint8(off + i, s.charCodeAt(i));
  };
  ascii(0, "RIFF");
  view.setUint32(4, 36 + bytes, true);
  ascii(8, "WAVE");
  ascii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  ascii(36, "data");
  view.setUint32(40, bytes, true);
  new Uint8Array(buf).set(new Uint8Array(samples.buffer, samples.byteOffset, samples.byteLength), 44);
  return new Blob([buf], { type: "audio/wav" });
}

function speechRecognitionLang(code) {
  const map = {
    en: "en-US",
    hi: "hi-IN",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    zh: "zh-CN",
    ja: "ja-JP",
    auto: "en-US",
  };
  return map[String(code || "en")] || "en-US";
}

class LiveCaptioner {
  constructor() {
    this._rec = null;
    this._wanted = false;
    this._fromIndex = 0;
    this._resetNext = false;
  }

  get supported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  resetUtterance() {
    this._resetNext = true;
  }

  start({ lang = "en-US", onText } = {}) {
    this.stop();
    this._fromIndex = 0;
    this._resetNext = false;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR || !onText) return false;
    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.lang = speechRecognitionLang(lang);
    rec.onresult = (ev) => {
      if (this._resetNext) {
        this._fromIndex = ev.resultIndex;
        this._resetNext = false;
      }
      const parts = [];
      for (let i = this._fromIndex; i < ev.results.length; i += 1) {
        const piece = (ev.results[i][0].transcript || "").replace(/\s+/g, " ").trim();
        if (piece) parts.push(piece);
      }
      const Q = window.QuestionText;
      const text = Q
        ? Q.collapseCaptionResults(parts)
        : parts.join(" ").replace(/\s+/g, " ").trim();
      if (text) onText(text, { interim: !ev.results[ev.results.length - 1].isFinal });
    };
    rec.onend = () => {
      if (!this._wanted) return;
      try { rec.start(); } catch (_) {}
    };
    rec.onerror = (ev) => {
      const err = ev && ev.error;
      if (err === "not-allowed" || err === "service-not-allowed") {
        this._wanted = false;
        return;
      }
      if (err === "no-speech" || err === "aborted") return;
    };
    this._rec = rec;
    this._wanted = true;
    try {
      rec.start();
      return true;
    } catch (_) {
      this._wanted = false;
      this._rec = null;
      return false;
    }
  }

  stop() {
    this._wanted = false;
    if (!this._rec) return;
    try { this._rec.onresult = null; this._rec.onend = null; this._rec.stop(); } catch (_) {}
    this._rec = null;
  }
}

function _openMicConstraints(deviceId) {
  const audio = {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 1,
  };
  if (deviceId) audio.deviceId = { exact: deviceId };
  return { audio };
}

async function findLoopbackDeviceId() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const hit = devices.find((d) => d.kind === "audioinput" && isLoopbackLabel(d.label));
    return hit ? hit.deviceId : "";
  } catch (_) {
    return "";
  }
}

class CallAudioCapture {
  constructor() {
    this.stream = null;
    this.kind = "none";
    this.recorder = null;
    this.chunks = [];
    this.recording = false;
    this.ctx = null;
    this.analyser = null;
    this._buf = null;
    this._vadTimer = null;
    this._inSpeech = false;
    this._questionOpen = false;
    this._onset = 0;
    this._silenceAt = 0;
    this._speechAt = 0;
    this.onUtterance = null;
    this.onLevel = null;
    this.onPartial = null;
    this.onSpeechStart = null;
    this._lastPartialAt = 0;
    this._src = null;
    this._pcmNode = null;
    this._pcmMute = null;
    this._pcmChunks = [];
    this._pcmTotal = 0;
    this.onPcmStream = null;
  }

  get live() {
    return !!(this.stream && this.stream.getAudioTracks().some((t) => t.readyState === "live"));
  }

  async acquireCallAudio() {
    const attempts = [
      {
        video: { frameRate: 1, width: 64, height: 64 },
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 2 },
        systemAudio: "include",
        preferCurrentTab: false,
        selfBrowserSurface: "exclude",
        monitorTypeSurfaces: "include",
      },
      { video: true, audio: true, systemAudio: "include" },
      { video: true, audio: true },
    ];
    let lastErr = null;
    for (const opts of attempts) {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia(opts);
        if (!stream.getAudioTracks().length) {
          stream.getTracks().forEach((t) => t.stop());
          lastErr = new Error("No audio in that share. Choose a tab/window and enable Share audio.");
          continue;
        }
        stream.getVideoTracks().forEach((t) => {
          t.enabled = false;
        });
        this._adopt(stream, "call");
        return "call";
      } catch (err) {
        lastErr = err;
        const name = err && err.name;
        if (name === "NotAllowedError" || name === "AbortError") break;
      }
    }
    throw lastErr || new Error("Call audio was not granted");
  }

  async acquireMic({ loopbackFirst = true } = {}) {
    // Permission first so device labels exist, then switch to a loopback cable if present.
    let stream = await navigator.mediaDevices.getUserMedia(_openMicConstraints(""));
    let kind = "mic";
    if (loopbackFirst) {
      const loopId = await findLoopbackDeviceId();
      if (loopId) {
        stream.getTracks().forEach((t) => t.stop());
        stream = await navigator.mediaDevices.getUserMedia(_openMicConstraints(loopId));
        kind = "loopback";
      }
    }
    this._adopt(stream, kind);
    return this.kind;
  }

  async acquirePreferred() {
    // Same path Mock already uses: mic permission hears YouTube/Meet from speakers or BlackHole.
    return this.acquireMic({ loopbackFirst: true });
  }

  _adopt(stream, kind) {
    this.stopTracksOnly();
    this.stream = stream;
    this.kind = kind;
    stream.getAudioTracks().forEach((t) => {
      t.addEventListener("ended", () => {
        if (this.kind === kind) this.kind = "none";
      });
    });
  }

  _mime() {
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) return "audio/webm;codecs=opus";
    if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
    return "";
  }

  async startHold() {
    // Hold-to-record: one clip from Listen until Stop & Process. Do not let VAD cut it.
    this.stopVad();
    this._questionOpen = true;
    this._inSpeech = true;
    this._resetPcm();
    this._wireAnalyser();
    return this.start();
  }

  startCaptionTap() {
    // Live STT / captions only — do not start a second MediaRecorder.
    this.stopVad();
    this._questionOpen = true;
    this._inSpeech = true;
    this._resetPcm();
    this._wireAnalyser();
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
  }

  async start() {
    if (!this.live) await this.acquireMic({ loopbackFirst: true });
    if (this.recording) return this.kind;
    this.chunks = [];
    const mime = this._mime();
    this.recorder = new MediaRecorder(this.stream, mime ? { mimeType: mime } : undefined);
    this.recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) this.chunks.push(e.data);
    };
    this.recorder.start(200);
    this.recording = true;
    this._lastPartialAt = Date.now();
    return this.kind;
  }

  snapshot() {
    if (!this.recording || !this.chunks.length) return null;
    const type = (this.recorder && this.recorder.mimeType) || "audio/webm";
    return new Blob(this.chunks, { type });
  }

  async stop() {
    if (!this.recording || !this.recorder) return null;
    const blob = await new Promise((resolve) => {
      this.recorder.onstop = () => {
        const type = this.recorder.mimeType || "audio/webm";
        resolve(new Blob(this.chunks, { type }));
      };
      try {
        this.recorder.stop();
      } catch (_) {
        resolve(null);
      }
    });
    this.recorder = null;
    this.recording = false;
    this.chunks = [];
    return blob;
  }

  async cancel() {
    this.stopVad();
    if (this.recorder && this.recording) {
      try { this.recorder.stop(); } catch (_) {}
    }
    this.recorder = null;
    this.recording = false;
    this.chunks = [];
  }

  stopTracksOnly() {
    this.cancel();
    this.stopMeter();
    if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
    this.stream = null;
    this.kind = "none";
    this._dropPcmTap();
    if (this.ctx) {
      try { this.ctx.close(); } catch (_) {}
      this.ctx = null;
      this.analyser = null;
      this._src = null;
    }
  }

  _resetPcm() {
    this._pcmChunks = [];
    this._pcmTotal = 0;
  }

  _dropPcmTap() {
    this._resetPcm();
    try { if (this._pcmNode) this._pcmNode.disconnect(); } catch (_) {}
    try { if (this._pcmMute) this._pcmMute.disconnect(); } catch (_) {}
    this._pcmNode = null;
    this._pcmMute = null;
  }

  _wirePcmTap() {
    if (this._pcmNode || !this.ctx || !this._src) return;
    if (!this.ctx.createScriptProcessor) return;
    const node = this.ctx.createScriptProcessor(4096, 1, 1);
    node.onaudioprocess = (ev) => {
      const input = ev.inputBuffer.getChannelData(0);
      if (this.onPcmStream) {
        try { this.onPcmStream(input); } catch (_) {}
      }
      // Keep PCM for the whole in-progress question, including short pauses
      // (same idea as concatenating AudioRecorder.frames until stop).
      if (!this._questionOpen && !this._inSpeech) return;
      this._pcmChunks.push(new Float32Array(input));
      this._pcmTotal += input.length;
      const cap = Math.floor((this.ctx.sampleRate || 48000) * 90);
      while (this._pcmTotal > cap && this._pcmChunks.length > 1) {
        this._pcmTotal -= this._pcmChunks[0].length;
        this._pcmChunks.shift();
      }
    };
    const mute = this.ctx.createGain();
    mute.gain.value = 0;
    this._src.connect(node);
    node.connect(mute);
    mute.connect(this.ctx.destination);
    this._pcmNode = node;
    this._pcmMute = mute;
  }

  snapshotPcmWav() {
    if (!this._pcmChunks.length || this._pcmTotal < 1600) return null;
    const rate = (this.ctx && this.ctx.sampleRate) || 48000;
    return encodeWavPcm(this._pcmChunks, rate);
  }

  _wireAnalyser() {
    if (this.analyser || !this.stream) return;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    this.ctx = this.ctx || new Ctx();
    this._src = this.ctx.createMediaStreamSource(this.stream);
    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 1024;
    this._src.connect(this.analyser);
    this._buf = new Uint8Array(this.analyser.fftSize);
    this._wirePcmTap();
  }

  startVad(onUtterance, opts = {}) {
    this.onUtterance = onUtterance;
    this.onPartial = opts.onPartial || null;
    this.onSpeechStart = opts.onSpeechStart || null;
    const endSilenceMs = opts.endSilenceMs || 2200;
    const minSpeechMs = opts.minSpeechMs || 400;
    const prefetchEveryMs = opts.prefetchEveryMs || 2000;
    this.stopVad();
    this._inSpeech = false;
    this._questionOpen = false;
    this._onset = 0;
    this._silenceAt = 0;
    this._speechAt = 0;
    this._vadBusy = false;
    this._lastPartialAt = 0;
    const emitPartial = () => {
      if (!this.onPartial) return;
      const wav = this.snapshotPcmWav();
      const snap = wav || this.snapshot();
      if (snap && snap.size > 600) {
        Promise.resolve(this.onPartial(snap)).catch(() => {});
      }
    };
    const tick = async () => {
      if (!this._vadTimer || this._vadBusy) return;
      this._vadBusy = true;
      try {
        if (!this.live) return;
        this._wireAnalyser();
        if (this.ctx && this.ctx.state === "suspended") await this.ctx.resume();
        const rms = _rmsFromAnalyser(this.analyser, this._buf);
        if (this.onLevel) this.onLevel(rms);
        const now = Date.now();
        if (rms >= 0.012) {
          this._onset += 1;
          this._silenceAt = 0;
          if (!this._inSpeech && this._onset >= 3) {
            this._inSpeech = true;
            if (!this._questionOpen) {
              this._questionOpen = true;
              this._speechAt = now;
              this._resetPcm();
              if (this.onSpeechStart) this.onSpeechStart();
              if (!this.recording) await this.start();
            }
            // Later sentences in the same question keep the PCM buffer
            // (do not wipe on every onset).
          }
          if (this._inSpeech && now - this._lastPartialAt >= prefetchEveryMs) {
            this._lastPartialAt = now;
            emitPartial();
          }
        } else {
          this._onset = 0;
          if (this._inSpeech) {
            if (!this._silenceAt) this._silenceAt = now;
            if (now - this._lastPartialAt >= prefetchEveryMs) {
              this._lastPartialAt = now;
              emitPartial();
            }
            const silent = now - this._silenceAt;
            const spoken = now - this._speechAt;
            // ~2.2s silence so a pause between sentences is not a cut.
            if (silent >= endSilenceMs && spoken >= minSpeechMs) {
              this._inSpeech = false;
              this._questionOpen = false;
              this._silenceAt = 0;
              const wav = this.snapshotPcmWav();
              const blob = await this.stop();
              const use = wav && wav.size > 800 ? wav : blob;
              this._resetPcm();
              if (use && this.onUtterance) await this.onUtterance(use);
            }
          }
        }
      } catch (_) { /* keep looping */ }
      finally {
        this._vadBusy = false;
      }
    };
    this._vadTimer = setInterval(tick, 90);
  }

  stopVad() {
    if (this._vadTimer) {
      clearInterval(this._vadTimer);
      this._vadTimer = null;
    }
    this._inSpeech = false;
    this._questionOpen = false;
  }

  attachWaveform(canvas) {
    this._waveCanvas = canvas || null;
  }

  startMeter(onLevel) {
    if (onLevel) this.onLevel = onLevel;
    this.stopMeter();
    const tick = async () => {
      if (!this._meterTimer) return;
      try {
        if (!this.live) return;
        this._wireAnalyser();
        if (this.ctx && this.ctx.state === "suspended") await this.ctx.resume();
        const rms = _rmsFromAnalyser(this.analyser, this._buf);
        if (this.onLevel) this.onLevel(rms);
        this._drawWave();
      } catch (_) { /* keep looping */ }
    };
    this._meterTimer = setInterval(tick, 40);
    tick();
  }

  stopMeter() {
    if (this._meterTimer) {
      clearInterval(this._meterTimer);
      this._meterTimer = null;
    }
  }

  _drawWave() {
    const canvas = this._waveCanvas;
    if (!canvas || !this.analyser) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const data = new Uint8Array(this.analyser.fftSize);
    this.analyser.getByteTimeDomainData(data);
    ctx.beginPath();
    ctx.lineWidth = 2.4;
    ctx.strokeStyle = "#22c55e";
    const step = Math.max(1, Math.floor(data.length / w));
    for (let x = 0; x < w; x += 1) {
      const v = data[x * step] || 128;
      const y = (v / 255) * h;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

async function captureScreenPng() {
  const attempts = [
    {
      video: { displaySurface: "browser" },
      audio: false,
      preferCurrentTab: false,
      selfBrowserSurface: "exclude",
      monitorTypeSurfaces: "include",
    },
    { video: true, audio: false },
  ];
  let stream = null;
  let lastErr = null;
  for (const opts of attempts) {
    try {
      stream = await navigator.mediaDevices.getDisplayMedia(opts);
      break;
    } catch (err) {
      lastErr = err;
      const name = err && err.name;
      if (name === "NotAllowedError" || name === "AbortError" || name === "NotFoundError") break;
    }
  }
  if (!stream) throw lastErr || new Error("Screen capture was blocked");
  try {
    const track = stream.getVideoTracks()[0];
    const settings = track.getSettings();
    const video = document.createElement("video");
    video.srcObject = stream;
    video.muted = true;
    await video.play();
    await new Promise((r) => setTimeout(r, 200));
    const canvas = document.createElement("canvas");
    canvas.width = settings.width || video.videoWidth || 1280;
    canvas.height = settings.height || video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    return blob;
  } finally {
    stream.getTracks().forEach((t) => t.stop());
  }
}

function floatToPcm16Base64(float32, srcRate, targetRate) {
  const inRate = srcRate || 48000;
  const outRate = targetRate || 24000;
  const ratio = inRate / outRate;
  const n = Math.max(1, Math.floor(float32.length / ratio));
  const pcm = new Int16Array(n);
  for (let i = 0; i < n; i += 1) {
    let s = float32[Math.min(float32.length - 1, Math.floor(i * ratio))] || 0;
    if (s > 1) s = 1;
    else if (s < -1) s = -1;
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  const bytes = new Uint8Array(pcm.buffer);
  let bin = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(bin);
}

class LiveTranscribeSocket {
  constructor(opts = {}) {
    this.engineId = opts.engineId || "";
    this.lang = opts.lang || "en";
    this.onDelta = opts.onDelta || null;
    this.onCompleted = opts.onCompleted || null;
    this.onSpeechStarted = opts.onSpeechStarted || null;
    this.onReady = opts.onReady || null;
    this.onError = opts.onError || null;
    this.ws = null;
    this.ready = false;
    this._closed = false;
  }

  connect() {
    this._closed = false;
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const qs = new URLSearchParams({
      engine_id: this.engineId,
      language: this.lang,
    });
    const ws = new WebSocket(`${proto}//${location.host}/api/stt/live?${qs}`);
    this.ws = ws;
    ws.onmessage = (ev) => {
      let data = {};
      try { data = JSON.parse(ev.data); } catch (_) { return; }
      const kind = data.type;
      if (kind === "ready") {
        this.ready = true;
        if (this.onReady) this.onReady(data.model);
      } else if (kind === "delta" && data.text && this.onDelta) {
        this.onDelta(data.text);
      } else if (kind === "completed" && this.onCompleted) {
        this.onCompleted(data.text || "");
      } else if (kind === "speech_started" && this.onSpeechStarted) {
        this.onSpeechStarted();
      } else if (kind === "error") {
        this.ready = false;
        if (this.onError) this.onError(data.message || "live stt error");
      }
    };
    ws.onerror = () => {
      this.ready = false;
      if (this.onError) this.onError("live stt socket error");
    };
    ws.onclose = () => {
      this.ready = false;
      if (!this._closed && this.onError) this.onError("live stt closed");
    };
  }

  pushFloat32(float32, sampleRate) {
    if (!this.ws || this.ws.readyState !== 1 || !float32 || !float32.length) return;
    const audio = floatToPcm16Base64(float32, sampleRate, 24000);
    if (!audio) return;
    try {
      this.ws.send(JSON.stringify({ type: "pcm", audio }));
    } catch (_) { /* drop if socket is busy */ }
  }

  commit() {
    if (!this.ws || this.ws.readyState !== 1) return;
    try { this.ws.send(JSON.stringify({ type: "commit" })); } catch (_) {}
  }

  close() {
    this._closed = true;
    this.ready = false;
    try { this.ws && this.ws.close(); } catch (_) {}
    this.ws = null;
  }
}

window.CallAudioCapture = CallAudioCapture;
window.MicRecorder = CallAudioCapture;
window.LiveCaptioner = LiveCaptioner;
window.encodeWavPcm = encodeWavPcm;
window.floatToPcm16Base64 = floatToPcm16Base64;
window.LiveTranscribeSocket = LiveTranscribeSocket;
window.speechRecognitionLang = speechRecognitionLang;
window.captureScreenPng = captureScreenPng;
window.findLoopbackDeviceId = findLoopbackDeviceId;
window.isLoopbackLabel = isLoopbackLabel;
