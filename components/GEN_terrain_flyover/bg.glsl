out vec4 fragColor;
uniform vec4 uA;   // horizonY, sun(0-1), glow, time
uniform vec4 uB;   // glow rgb, 0
void main(){
  vec2 uv = vUV.st; float asp = uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  float hy = uA.x;
  float dy = uv.y - hy;
  vec3 col = vec3(0.004,0.004,0.006);
  float g = exp(-abs(dy)*9.0)*0.5*uA.z;
  col += uB.rgb*g*step(-0.02,dy)*1.0 + uB.rgb*g*0.25*step(dy,-0.02);
  // sun: half disc above the horizon with scanline cutouts
  vec2 sp = vec2((uv.x-0.5)*asp, dy);
  float r = 0.20;
  float d = length(sp - vec2(0.0, 0.07));
  float disc = smoothstep(r, r-0.004, d) * step(0.0, dy);
  float band = step(0.5, fract((dy*38.0))) ;
  float cut = mix(1.0, band, smoothstep(0.02, 0.2, 0.2 - sp.y + 0.0) );
  col = mix(col, vec3(1.0,0.96,0.88)*0.9, disc*cut*uA.y);
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
