// Initial chemical state: R = A (1), G = B (seeded from the image + sprinkled blobs).
// Input0 = image (src, already switched with the demo image).
out vec4 fragColor;
uniform vec4 uSeedA;   // x seed amount, y threshold, z invert, w sprinkle density
uniform vec2 uRes;
uniform float uSeed;
float hash2(vec2 p){ vec3 q = fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)+uSeed*0.011); q += dot(q,q.yzx+33.33); return fract((q.x+q.y)*q.z); }
void main(){
    vec2 uv = vUV.st;
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    float L = dot(c, vec3(0.299, 0.587, 0.114));
    L = mix(L, 1.0 - L, uSeedA.z);
    float b = uSeedA.x * smoothstep(uSeedA.y, uSeedA.y + 0.08, L);
    // random blobs on a coarse grid so even a flat image grows something
    float cells = 16.0;
    vec2 g = uv*cells*vec2(uRes.x/uRes.y, 1.0);
    vec2 id = floor(g), f = fract(g) - 0.5;
    float r = hash2(id);
    vec2 off = (vec2(hash2(id+7.3), hash2(id+13.1)) - 0.5)*0.5;
    float blob = 1.0 - step(0.0, length(f-off) - (0.10 + 0.12*hash2(id+3.7)));
    if (r > 1.0 - 0.2*uSeedA.w) b = max(b, blob);
    fragColor = TDOutputSwizzle(vec4(1.0 - 0.5*b, b, 0.0, 1.0));
}
