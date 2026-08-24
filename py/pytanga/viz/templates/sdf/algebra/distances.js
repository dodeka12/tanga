// Distance-function GLSL snippet registry.
//
// Keys are shared with Python `DistanceFunction.value` (sdf/distance.py). Each
// snippet is a pure function of the result coefficient vector `r[]` (plus, for
// `grade`/`component`, a compile-time integer parameter). The snippets rely on
// compile-time constants the algebra binding (Phase 8) emits before them:
//   · `const int NR;`          — result vector size
//   · `const int SLOT_PSEUDO;` — pseudoscalar coefficient slot (scalar is 0)
//
// `grade` depends on `gradeNorm(in float r[NR], int k)`, which is assembled by
// the algebra binding because the grade→slot mapping is algebra-specific; its
// full body lands in Phase 8. The snippet itself is registered here so
// distance-function selection is a registry lookup with no branching.
//
// Each entry also carries a `derivative` note — the closed-form `g[k] = ∂D/∂r[k]`
// formula. The concrete `g[k]` GLSL is emitted per result mask by `eval.js`
// (Phase 13), where the mask's slot indices are known; the string documents the
// contract that emission implements.

export const distanceFuncs = new Map([
    ['scalar_pseudo', {
        params: [],
        derivative: '1.0 at the scalar (slot 0) and pseudo (slot SLOT_PSEUDO) slots; r[k]·invRest otherwise',
        snippet: `
float distOfScalarPseudo(in float r[NR]) {
    float rest = 0.0;
    for (int i = 0; i < NR; i++) {
        if (i != 0 && i != SLOT_PSEUDO) rest += r[i] * r[i];
    }
    return r[0] + r[SLOT_PSEUDO] + sqrt(rest);
}`,
    }],
    ['magnitude', {
        params: [],
        derivative: 'r[k]·invNorm over the whole vector (invNorm = 1/sqrt(Σr²))',
        snippet: `
float distOfMagnitude(in float r[NR]) {
    float s = 0.0;
    for (int i = 0; i < NR; i++) s += r[i] * r[i];
    return sqrt(s);
}`,
    }],
    ['scalar', {
        params: [],
        derivative: 'δ[k, 0] (1.0 at the scalar slot, 0.0 elsewhere)',
        snippet: `
float distOfScalar(in float r[NR]) {
    return r[0];
}`,
    }],
    ['grade', {
        params: ['k'],
        derivative: 'r[k]·invGrade on the selected grade (bitCount(RESULT_IDS[k]) == k), else 0',
        snippet: `
float distOfGrade(in float r[NR], int k) {
    return gradeNorm(r, k);
}`,
    }],
    ['component', {
        params: ['blade_id'],
        derivative: 'δ[k, blade_id] (1.0 at the selected slot, 0.0 elsewhere)',
        snippet: `
float distOfComponent(in float r[NR], int blade_id) {
    return r[blade_id];
}`,
    }],
]);