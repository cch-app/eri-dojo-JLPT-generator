/** localStorage that never throws (private mode, quota, disabled storage). */
export const safeStorage = {
  get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (e) {
      // ignore: progress simply won't persist
    }
  },
};
