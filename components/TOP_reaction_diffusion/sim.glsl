// Gray-Scott driven by an image. Input0 = previous state (R=A, G=B), input1 = image.
// Run `Steps` times per frame via the TOP's Num Passes.
out vec4 fragColor;
uniform vec4 uRate;    // x feed, y kill, z Da, w Db
uniform vec4 uDrive;   // x feed influence, y kill influence, z inject per pass, w seed threshold
uniform vec4 uMisc;    // x dt, y play, z invert luminance, w unused
void main(){
    vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[0], 0));
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    if (uMisc.y < 0.5) { fragColor = TDOutputSwizzle(c); return; }
    vec3 im = texture(sTD2DInputs[1], uv).rgb;
    float L = dot(im, vec3(0.299, 0.587, 0.114));
    L = mix(L, 1.0 - L, uMisc.z);
    float feed = max(uRate.x + uDrive.x * 0.03 * (L - 0.5), 0.0);
    float kill = max(uRate.y + uDrive.y * 0.012 * (L - 0.5), 0.0);
    vec2 lap = -c.rg;
    lap += 0.2  * (texture(sTD2DInputs[0], uv+vec2( px.x,0)).rg + texture(sTD2DInputs[0], uv+vec2(-px.x,0)).rg
                 + texture(sTD2DInputs[0], uv+vec2(0, px.y)).rg + texture(sTD2DInputs[0], uv+vec2(0,-px.y)).rg);
    lap += 0.05 * (texture(sTD2DInputs[0], uv+px).rg + texture(sTD2DInputs[0], uv-px).rg
                 + texture(sTD2DInputs[0], uv+vec2(px.x,-px.y)).rg + texture(sTD2DInputs[0], uv+vec2(-px.x,px.y)).rg);
    float a = c.r, b = c.g;
    float abb = a*b*b;
    float na = a + (uRate.z*lap.x - abb + feed*(1.0-a)) * uMisc.x;
    float nb = b + (uRate.w*lap.y + abb - (kill+feed)*b) * uMisc.x;
    // continuous injection: bright (or dark if inverted) image areas keep seeding chemical B
    nb += uDrive.z * smoothstep(uDrive.w, uDrive.w + 0.08, L) * (1.0 - nb);
    fragColor = TDOutputSwizzle(vec4(clamp(na,0.0,1.0), clamp(nb,0.0,1.0), 0.0, 1.0));
}
