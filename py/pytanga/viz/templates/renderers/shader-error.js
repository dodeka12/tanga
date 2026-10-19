// Shader compile/link error reporting — shared between the live viewer and the
// standalone SDF viewer.
//
// three.js reports shader failures through `renderer.debug.onShaderError` when a
// program first compiles/links.  `installShaderErrorHook` formats the driver
// info log with source context and forwards it to `onError` (which the main
// viewer routes through `sendLog` to the backend `on_shader_error` handler).

export function formatShaderError(gl, shader, type) {
    const log = gl.getShaderInfoLog(shader).trim();
    const source = gl.getShaderSource(shader);
    const m = /ERROR: 0:(\d+)/.exec(log);
    if (!m) return `${type}\n\n${log}`;
    const errLine = parseInt(m[1], 10);
    const lines = source.split('\n');
    const from = Math.max(errLine - 6, 0);
    const to = Math.min(errLine + 6, lines.length);
    const ctx = [];
    for (let i = from; i < to; i++) {
        ctx.push(`${i + 1 === errLine ? '>' : ' '} ${i + 1}: ${lines[i]}`);
    }
    return `${type}\n\n${log}\n\n${ctx.join('\n')}`;
}

export function installShaderErrorHook(renderer, onError) {
    if (!renderer || !renderer.debug) return () => {};
    const prev = renderer.debug.onShaderError;
    renderer.debug.onShaderError = (gl, program, glVertexShader, glFragmentShader) => {
        const parts = [
            'THREE.WebGLProgram: Shader Error',
            'VALIDATE_STATUS ' + gl.getProgramParameter(program, gl.VALIDATE_STATUS),
            'Program Info Log: ' + gl.getProgramInfoLog(program).trim(),
            formatShaderError(gl, glVertexShader, 'VERTEX'),
            formatShaderError(gl, glFragmentShader, 'FRAGMENT'),
        ];
        onError(parts.join('\n\n'));
    };
    return () => {
        renderer.debug.onShaderError = prev;
    };
}
