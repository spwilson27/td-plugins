uniform vec4 uRes;   // w, h, margin px, border px
uniform vec4 uCol;   // rgb, opacity
uniform vec4 uAcc;   // accent rgb, accent on
uniform vec4 uF;     // marks, border, ticks, cross
out vec4 fragColor;

float cov(float d){ return clamp(0.5 - d, 0.0, 1.0); }   // d = signed distance in px (negative inside)

void main(){
    vec2 p = vUV.st * uRes.xy;
    vec2 c = uRes.xy * 0.5;
    float H = uRes.y;
    float inset = uRes.z * 0.5;
    vec2 hs = c - vec2(inset);
    vec2 e = hs - abs(p - c);            // distance inward from each edge pair
    float col_a = 0.0, acc_a = 0.0;

    // thin border
    if (uF.y > 0.5) {
        float sd = min(e.x, e.y);          // >0 inside the rect
        col_a = max(col_a, cov(abs(sd) - uRes.w * 0.5));
    }
    // corner brackets
    if (uF.x > 0.5) {
        float t = max(2.0, uRes.w * 2.5), L = 0.035 * H;
        float h = cov(abs(e.y) - t * 0.5) * step(-t * 0.5, e.x) * step(e.x, L);
        float v = cov(abs(e.x) - t * 0.5) * step(-t * 0.5, e.y) * step(e.y, L);
        float br = max(h, v);
        bool tl = (p.x < c.x && p.y > c.y);
        if (tl && uAcc.w > 0.5) acc_a = max(acc_a, br); else col_a = max(col_a, br);
    }
    // centre cross
    if (uF.w > 0.5) {
        vec2 q = abs(p - c);
        float L = 0.012 * H;
        float cr = max(cov(q.y - 0.5) * step(q.x, L), cov(q.x - 0.5) * step(q.y, L));
        col_a = max(col_a, cr);
    }
    // edge ticks (top & bottom, along the safe rect)
    if (uF.z > 0.5) {
        float W = hs.x * 2.0;
        float sp = W / 40.0;
        float u = (p.x - (c.x - hs.x)) / sp;
        float idx = floor(u + 0.5);
        float dx = abs(u - idx) * sp;
        float len = (mod(idx, 5.0) < 0.5) ? 0.012 * H : 0.006 * H;
        float inX = step(0.0, idx) * step(idx, 40.0);
        float onT = cov(dx - 0.5) * inX * step(0.0, e.y) * step(e.y, len) * step(c.y - hs.y, abs(p.y - c.y)) * step(0.9, step(abs(p.y - c.y), hs.y + 1.0));
        col_a = max(col_a, onT);
    }
    vec3 rgb = mix(uCol.rgb * col_a, uAcc.rgb, acc_a);
    float a = clamp(max(col_a, acc_a), 0.0, 1.0) * uCol.w;
    fragColor = TDOutputSwizzle(vec4(rgb * uCol.w, a));
}
