// Runs Python (Pyodide) off the page's main thread, so a stuck loop in your
// answer can be stopped by terminating this worker.
// Messages in:  {type: "init", checker}  then  {type: "check", id, kind, card, answer}
// Messages out: {type: "ready"} | {type: "failed", error} | {type: "result", id, result}

let pyodide = null;

self.onmessage = async (event) => {
  const msg = event.data;
  if (msg.type === "init") {
    try {
      // Fail fast where the page's security policy forbids WebAssembly: Pyodide itself would just hang.
      new WebAssembly.Module(new Uint8Array([0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00]));
    } catch (err) {
      self.postMessage({ type: "failed", error: "this page isn't allowed to run WebAssembly (" + String(err && err.message || err) + ")" });
      return;
    }
    try {
      importScripts("pyodide/pyodide.js");
      pyodide = await loadPyodide({ indexURL: new URL("pyodide/", self.location.href).href });
      pyodide.runPython(msg.checker);
      self.postMessage({ type: "ready" });
    } catch (err) {
      self.postMessage({ type: "failed", error: String(err && err.message || err) });
    }
    return;
  }
  if (msg.type === "check") {
    let result;
    try {
      const checkJson = pyodide.globals.get("check_json");
      result = JSON.parse(checkJson(msg.kind, JSON.stringify(msg.card), msg.answer));
      checkJson.destroy();
    } catch (err) {
      result = { ok: false, msg: "The checker crashed: " + String(err && err.message || err) };
    }
    self.postMessage({ type: "result", id: msg.id, result });
  }
};
