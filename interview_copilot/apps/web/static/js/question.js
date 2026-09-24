/** Assemble a full interview question from paused / fragmented speech.
 * Keep in sync with packages/stt/question_text.py
 */
(() => {
  const TRAILING_INCOMPLETE =
    /(?:,|:|;|-|—|\/|\band\b|\bor\b|\bbut\b|\bthe\b|\ba\b|\ban\b|\bto\b|\bof\b|\bfor\b|\bwith\b|\bthat\b|\bwhich\b|\bwho\b|\bhow\b|\bwhat\b|\bwhen\b|\bwhy\b|\bcan\b|\bcould\b|\bwould\b|\bshould\b|\bis\b|\bare\b|\bwas\b|\byour\b|\bmy\b|\bin\b|\bon\b)\s*$/i;
  const END_PUNCT = /[.?!]["')\]]*\s*$/;
  const QUESTION_MARK = /\?\s*$/;
  const SHORT_PAUSE_MS = 900;
  const MERGE_WINDOW_MS = 3200;
  const ANSWER_SILENCE_MS = 1500;
  const INCOMPLETE_SILENCE_MS = 2200;
  const TRAILING_CONTINUE =
    /(?:\blike\b|\bsuch as\b|\bfor example\b|\bspecifically\b|\bincluding\b|\bbasically\b|\bmaybe\b|\bperhaps\b|\bso\b|\bthen\b|\balso\b|\bplus\b|\bwhich\b|\bwhere\b)\s*$/i;

  function wordCount(text) {
    return String(text || "")
      .split(/\s+/)
      .filter(Boolean).length;
  }

  function isIncompleteQuestion(text) {
    const t = String(text || "").trim();
    if (!t) return true;
    if (TRAILING_INCOMPLETE.test(t) || TRAILING_CONTINUE.test(t)) return true;
    const wc = wordCount(t);
    if (QUESTION_MARK.test(t) && wc >= 4) return false;
    if (END_PUNCT.test(t)) return wc < 8;
    return wc < 16;
  }

  function answerHoldMs(text) {
    if (isIncompleteQuestion(text)) return INCOMPLETE_SILENCE_MS;
    if (QUESTION_MARK.test(String(text || "").trim()) && wordCount(text) >= 5) return 1200;
    return ANSWER_SILENCE_MS;
  }

  function questionReadyToAnswer(text, quietMs, speaking = false) {
    if (speaking) return false;
    const t = String(text || "").trim();
    if (!t) return false;
    if (quietMs < answerHoldMs(t)) return false;
    if (looksLikeQuestion(t)) return true;
    return wordCount(t) >= 12;
  }

  function collapseRepeatedPhrase(text) {
    const words = String(text || "").split(/\s+/).filter(Boolean);
    const n = words.length;
    if (n < 4) return words.join(" ");
    const mid = Math.floor(n / 2);
    if (words.slice(0, mid).join(" ") === words.slice(mid, mid * 2).join(" ") && n - mid * 2 <= 1) {
      return words.slice(0, mid).join(" ");
    }
    for (let size = 2; size <= mid; size += 1) {
      if (n < size * 2) break;
      const chunk = words.slice(0, size).join(" ");
      if (words.slice(0, size * 2).join(" ") === `${chunk} ${chunk}`) {
        return `${chunk} ${words.slice(size * 2).join(" ")}`.trim();
      }
    }
    return words.join(" ");
  }

  function wordKey(w) {
    return String(w || "").toLowerCase().replace(/[^a-z0-9']+/g, "");
  }

  function collapseRevisionLoops(text) {
    let words = String(text || "").split(/\s+/).filter(Boolean);
    for (let g = 0; g < 24; g += 1) {
      const n = words.length;
      if (n < 16) break;
      let removed = false;
      const maxW = Math.min(14, Math.floor(n / 2));
      for (let width = maxW; width >= 5; width -= 1) {
        const first = new Map();
        for (let i = 0; i <= n - width; i += 1) {
          const keys = words.slice(i, i + width).map(wordKey);
          if (!keys.every(Boolean)) continue;
          const key = keys.join("\0");
          if (first.has(key)) {
            const j = first.get(key);
            if (i - j < width) continue;
            words = words.slice(0, j).concat(words.slice(i));
            removed = true;
            break;
          }
          first.set(key, i);
        }
        if (removed) break;
      }
      if (!removed) break;
    }
    return words.join(" ");
  }

  function maxSharedNgram(a, b, minN = 5) {
    const ka = String(a || "").split(/\s+/).map(wordKey).filter(Boolean);
    const kb = String(b || "").split(/\s+/).map(wordKey).filter(Boolean);
    if (ka.length < minN || kb.length < minN) return 0;
    const top = Math.min(14, ka.length, kb.length);
    for (let width = top; width >= minN; width -= 1) {
      const other = new Set();
      for (let i = 0; i <= kb.length - width; i += 1) {
        other.add(kb.slice(i, i + width).join("\0"));
      }
      for (let i = 0; i <= ka.length - width; i += 1) {
        if (other.has(ka.slice(i, i + width).join("\0"))) return width;
      }
    }
    return 0;
  }

  function collapseSnowball(text) {
    let t = collapseRepeatedPhrase(String(text || "").replace(/\s+/g, " ").trim());
    if (!t) return t;
    t = collapseRevisionLoops(t);
    let prev = null;
    while (prev !== t) {
      prev = t;
      const words = t.split(/\s+/).filter(Boolean);
      if (words.length < 14) break;
      const stem = words.slice(0, 6).join(" ").toLowerCase();
      const last = t.toLowerCase().lastIndexOf(stem);
      if (last > 8) {
        t = collapseRevisionLoops(collapseRepeatedPhrase(t.slice(last).trim()));
      } else break;
    }
    return collapseRevisionLoops(t);
  }

  function stemLen(a, b) {
    const wa = String(a || "").toLowerCase().split(/\s+/).filter(Boolean);
    const wb = String(b || "").toLowerCase().split(/\s+/).filter(Boolean);
    let n = 0;
    for (let i = 0; i < Math.min(wa.length, wb.length); i += 1) {
      if (wa[i] !== wb[i]) break;
      n += 1;
    }
    return n;
  }

  function coalesceTranscript(prev, nxt) {
    const a = collapseSnowball(prev || "");
    const b = collapseSnowball(nxt || "");
    if (!a) return b;
    if (!b) return a;
    const al = a.toLowerCase();
    const bl = b.toLowerCase();
    if (al === bl) return b.length >= a.length ? b : a;
    const shared = maxSharedNgram(a, b);
    if (stemLen(a, b) >= 5) return wordCount(b) >= wordCount(a) ? b : a;
    if (shared >= 5) {
      const wa = wordCount(a);
      const wb = wordCount(b);
      if (wa > wb * 1.5 && wb >= 6) return b;
      return wb >= wa ? b : a;
    }
    if (al.includes(bl)) return a;
    if (bl.includes(al)) return b;
    return collapseSnowball(mergeFragments(a, b));
  }

  function collapseCaptionResults(parts) {
    let out = "";
    for (const part of parts || []) {
      const piece = String(part || "").replace(/\s+/g, " ").trim();
      if (!piece) continue;
      out = coalesceTranscript(out, piece);
    }
    return collapseSnowball(out);
  }

  function mergeFragments(prev, nxt) {
    const a = String(prev || "").trim();
    const b = String(nxt || "").trim();
    if (!a) return b;
    if (!b) return a;
    if (b.toLowerCase().includes(a.toLowerCase()) && b.length >= a.length) return b;
    if (a.toLowerCase().includes(b.toLowerCase())) return a;
    if (a.endsWith("-") || a.endsWith("—")) return a.replace(/[-—]+\s*$/, "") + b;
    const gap = a.endsWith(" ") || a.endsWith("\n") ? "" : " ";
    return `${a}${gap}${b}`;
  }

  function shouldMergeFragments(prev, nxt, gapMs) {
    if (!String(prev || "").trim() || !String(nxt || "").trim()) return false;
    if (gapMs > MERGE_WINDOW_MS) return false;
    if (isIncompleteQuestion(prev)) return true;
    if (gapMs <= SHORT_PAUSE_MS) return true;
    if (/^[a-z]/.test(String(nxt).trim())) return true;
    return false;
  }

  function isCloseEnoughForPrefetch(partial, full) {
    const a = String(partial || "").trim().toLowerCase();
    const b = String(full || "").trim().toLowerCase();
    if (!a || !b) return false;
    if (b.startsWith(a) && b.length - a.length <= 80) return true;
    if (a.startsWith(b)) return true;
    const n = Math.min(a.length, b.length, 48);
    return n >= 24 && a.slice(0, n) === b.slice(0, n);
  }

  function nextWordChunk(shown, want) {
    shown = String(shown || "");
    want = String(want || "");
    if (!want || shown === want) return null;
    if (!shown) {
      const m = want.match(/^\S+\s*/);
      return m ? m[0] : want;
    }
    if (want.startsWith(shown)) {
      const rest = want.slice(shown.length);
      const m = rest.match(/^\s*\S+\s*/);
      return m ? m[0] : rest;
    }
    const m = want.match(/^\S+\s*/);
    return m ? m[0] : want;
  }

  function questionTypeChunks(suffix) {
    const s = String(suffix || "");
    if (!s) return [];
    if (s.includes("\n") || s.includes("ANSWER:")) return [s];
    const parts = s.split(" ");
    const out = [];
    for (let i = 0; i < parts.length; i += 1) {
      if (i < parts.length - 1) out.push(`${parts[i]} `);
      else if (parts[i]) out.push(parts[i]);
    }
    return out.filter(Boolean);
  }

  function looksLikeQuestion(text) {
    const t = String(text || "").trim();
    if (t.length < 8) return false;
    const lower = t.toLowerCase();
    const markers = [
      "?", "tell me", "describe", "explain", "how do", "how does", "how would",
      "what is", "what are", "what would", "walk me", "walk through", "can you",
      "could you", "would you", "why did", "why do",
    ];
    if (markers.some((m) => lower.includes(m))) return true;
    return wordCount(t) >= 12;
  }

  window.QuestionText = {
    SHORT_PAUSE_MS,
    MERGE_WINDOW_MS,
    ANSWER_SILENCE_MS,
    INCOMPLETE_SILENCE_MS,
    wordCount,
    isIncompleteQuestion,
    answerHoldMs,
    questionReadyToAnswer,
    mergeFragments,
    shouldMergeFragments,
    isCloseEnoughForPrefetch,
    looksLikeQuestion,
    nextWordChunk,
    questionTypeChunks,
    collapseRepeatedPhrase,
    collapseSnowball,
    collapseRevisionLoops,
    coalesceTranscript,
    collapseCaptionResults,
  };
})();
