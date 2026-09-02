// Tanga Viewer — dialog manager.  Owns the id → `DialogView` map for global
// dialogs mounted on the shared full-screen `OverlayView`.

import { getOverlay } from './overlay.js';
import { DialogView } from './views/dialog-view.js';
import { FileChooserDialogView } from './views/file-chooser-dialog-view.js';

const _dialogs = new Map();

export function handleDialogDefine(msg, ws) {
    _removeDialog(msg.id);
    const isFileChooser = msg.variant === 'file_chooser';
    const view = isFileChooser
        ? new FileChooserDialogView({
            id: msg.id,
            title: msg.title,
            content: msg.content,
            align_x: msg.align_x,
            align_y: msg.align_y,
            dismissable: msg.dismissable,
            width: msg.width,
            height: msg.height,
            ws: ws,
        })
        : new DialogView({
            id: msg.id,
            title: msg.title,
            content: msg.content,
            align_x: msg.align_x,
            align_y: msg.align_y,
            dismissable: msg.dismissable,
            width: msg.width,
            height: msg.height,
            ws: ws,
        });
    _dialogs.set(msg.id, view);
    getOverlay().addChild(view);
}

export function handleDialogRemove(msg) {
    _removeDialog(msg.id);
}

export function handleDialogClear() {
    for (const id of [..._dialogs.keys()]) _removeDialog(id);
}

function _removeDialog(id) {
    const view = _dialogs.get(id);
    if (!view) return;
    _dialogs.delete(id);
    getOverlay().removeChild(view);
    view.destroy();
}
