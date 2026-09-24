"""Near-real-time live caption helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO_JS = ROOT / "apps/web/static/js/audio.js"


def test_encode_wav_pcm_writes_riff_header():
    script = r"""
const fs = require("fs");
const vm = require("vm");
class Blob {
  constructor(parts, opts = {}) {
    const chunks = parts.map((p) => (p instanceof ArrayBuffer ? Buffer.from(p) : Buffer.from(p)));
    this._buf = Buffer.concat(chunks);
    this.type = opts.type || "";
    this.size = this._buf.length;
  }
  async arrayBuffer() {
    return this._buf.buffer.slice(this._buf.byteOffset, this._buf.byteOffset + this._buf.byteLength);
  }
}
const ctx = {
  window: {},
  Blob,
  navigator: {},
  console,
  MediaRecorder: { isTypeSupported: () => false },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const blob = ctx.encodeWavPcm([new Float32Array([0, 0.5, -0.5, 1])], 16000);
if (!blob || blob.size < 44) {
  console.error("empty");
  process.exit(1);
}
const buf = blob._buf;
if (buf.slice(0, 4).toString() !== "RIFF" || buf.slice(8, 12).toString() !== "WAVE") {
  console.error("bad header", buf.slice(0, 12).toString());
  process.exit(1);
}
console.log("ok", blob.size);
"""
    proc = subprocess.run(
        ["node", "-e", script, str(AUDIO_JS)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout


def test_live_captioner_does_not_append_growing_finals():
    audio = AUDIO_JS.read_text(encoding="utf-8")
    question = (ROOT / "apps/web/static/js/question.js").read_text(encoding="utf-8")
    assert "_finalAcc" not in audio
    assert "text += ev.results" not in audio
    assert "collapseCaptionResults" in audio
    assert "collapseCaptionResults" in question
    assert "collapseSnowball" in question
    assert "collapseRevisionLoops" in question
    app = (ROOT / "apps/web/static/js/app.js").read_text(encoding="utf-8")
    assert "LEFT_CAPTION_IDLE" in app
    assert "live && cleaned" in app
    assert "live: !commit" in app
