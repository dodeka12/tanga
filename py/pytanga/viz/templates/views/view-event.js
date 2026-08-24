// Tanga Viewer — `ViewEvent`: a native `Event` carrying a typed payload.

/**
 * An `Event` with a `detail` payload.  Keeps `View` on the native `EventTarget`
 * substrate while giving event handlers ergonomic, typed payload access.
 */
export class ViewEvent extends Event {
    constructor(type, detail) {
        super(type);
        this.detail = detail;
    }
}
