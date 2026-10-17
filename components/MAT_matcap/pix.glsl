uniform sampler2D uMatcap;
uniform vec4 uA;    // rotate (rad), brightness, tint amount, flip y
uniform vec3 uTint;
in vec3 vNrmView;
layout(location = 0) out vec4 fragColor;
void main(){
    vec3 n = normalize(vNrmView);
    vec2 p = n.xy;
    float cs = cos(uA.x), sn = sin(uA.x);
    p = vec2(cs * p.x - sn * p.y, sn * p.x + cs * p.y);
    if (uA.w > 0.5) p.y = -p.y;
    vec3 c = texture(uMatcap, p * 0.5 + 0.5).rgb;
    c = mix(c, c * uTint, uA.z);
    c *= uA.y;
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
