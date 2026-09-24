/** Thin fetch helpers for Interview Copilot web API. */
const API = {
  async json(path, opts = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) {}
      throw new Error(detail);
    }
    return res.json();
  },

  get(path) {
    return this.json(path);
  },

  post(path, body) {
    return this.json(path, { method: "POST", body: JSON.stringify(body) });
  },

  patch(path, body) {
    return this.json(path, { method: "PATCH", body: JSON.stringify(body) });
  },

  put(path, body) {
    return this.json(path, { method: "PUT", body: JSON.stringify(body) });
  },

  del(path) {
    return this.json(path, { method: "DELETE" });
  },

  /**
   * Consume SSE from a POST that returns text/event-stream.
   * handlers: { onEvent(obj), onError(err), onDone() }
   */
  async streamPost(path, body, handlers = {}) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(await res.text());
    }
    return this._readSSE(res, handlers);
  },

  async streamForm(path, formData, handlers = {}) {
    const res = await fetch(path, { method: "POST", body: formData });
    if (!res.ok) {
      throw new Error(await res.text());
    }
    return this._readSSE(res, handlers);
  },

  async _readSSE(res, handlers) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const chunks = buf.split("\n\n");
      buf = chunks.pop() || "";
      for (const chunk of chunks) {
        const line = chunk.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        try {
          const obj = JSON.parse(line.slice(6));
          handlers.onEvent && handlers.onEvent(obj);
          if (obj.type === "done") handlers.onDone && handlers.onDone(obj);
          if (obj.type === "error") handlers.onError && handlers.onError(new Error(obj.message || "stream error"));
        } catch (e) {
          handlers.onError && handlers.onError(e);
        }
      }
    }
  },
};
