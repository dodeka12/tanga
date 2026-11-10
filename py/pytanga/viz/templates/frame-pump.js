// Tanga — frame pump. Serializes frame application for the animated export:
// at most one apply in flight, the newest requested target wins (a stale
// pending target is dropped), and a request issued from inside `apply` is
// queued rather than re-entering the apply function.
//
// Pure module: no DOM, no three.js, no imports — the export pipeline strips
// `import`/`export` and concatenates this into the library scope, and the
// unit tests import it directly with `node --test`.

/**
 * Create a frame pump around an async apply function.
 *
 * Contract:
 * - `request(n)` returns a promise that resolves when the pump is next idle
 *   (coalesced requests resolve too — the caller can ignore it).
 * - `busy` is true while an apply is in flight.
 * - `idle()` resolves immediately when idle, otherwise when the current run
 *   finishes.
 * - A rejecting `apply` is reported to `onError` (never rethrown, so a
 *   `requestAnimationFrame`-driven loop survives), the stale target is
 *   cleared, and the pump returns to idle.
 *
 * @param {(n: any) => Promise<void>} apply
 * @param {(err: unknown) => void} [onError]
 * @returns {{ request: (n: any) => Promise<void>, busy: boolean, idle: () => Promise<void> }}
 */
export function createFramePump(apply, onError = (err) => console.error(err)) {
    let running = false;
    let pending = null;
    let waiters = [];

    function settle() {
        running = false;
        const w = waiters;
        waiters = [];
        for (const resolve of w) resolve();
    }

    async function drain() {
        running = true;
        try {
            while (pending !== null) {
                const n = pending;
                pending = null;
                try {
                    await apply(n);
                } catch (err) {
                    pending = null; // drop the stale target
                    onError(err);   // never rethrow: rAF loop must survive
                    break;
                }
            }
        } finally {
            settle();
        }
    }

    function whenIdle() {
        if (!running) return Promise.resolve();
        return new Promise((resolve) => waiters.push(resolve));
    }

    return {
        request(n) {
            pending = n; // newest target wins (coalesced)
            if (!running) drain(); // fire-and-forget
            return whenIdle();
        },
        get busy() {
            return running;
        },
        idle() {
            return whenIdle();
        },
    };
}
