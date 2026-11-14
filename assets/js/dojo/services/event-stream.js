/**
 * Open a JSON server-sent-event stream. Calls onMessage(obj) per event and
 * onDrop() if the connection dies; returns a close() function.
 */
export function openEventStream(url, { onMessage, onDrop }, EventSourceImpl = window.EventSource) {
  const src = new EventSourceImpl(url);
  let closed = false;
  const close = () => {
    closed = true;
    src.close();
  };
  src.onmessage = (ev) => {
    let msg;
    try {
      msg = JSON.parse(ev.data);
    } catch (e) {
      return;
    }
    onMessage(msg, close);
  };
  src.onerror = () => {
    if (closed) return;
    close();
    onDrop && onDrop();
  };
  return close;
}
