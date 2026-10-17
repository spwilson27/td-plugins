// mat_porcelain: porcelain / bone / marble / nero marble. Object-space (no UVs).
uniform vec4 uP0; // x=style, y=gloss, z=sss, w=warp
uniform vec4 uP1; // x=vein amount, y=vein scale, z=crack amount, w=crack scale
uniform vec4 uP2; // x=crack width, y=bump (crack depth), z=thickness scale, w=unused
uniform vec4 uTint; // rgb multiplies base color
uniform vec4 uVeinC; // rgb vein tint multiplier

out vec4 oFragColor;

void styleData(int s, out vec3 base, out vec3 vein, out vec3 sssT, out float rough, out float coat, out float vmul, out float cloud, out float vscale){
  if(s==0){ base=vec3(.93,.92,.88); vein=vec3(.52,.60,.74); sssT=vec3(.95,.48,.38); rough=.10; coat=1.0; vmul=.40; cloud=.04; vscale=1.0; }
  else if(s==1){ base=vec3(.80,.73,.58); vein=vec3(.38,.26,.14); sssT=vec3(.85,.52,.28); rough=.42; coat=.18; vmul=.85; cloud=.30; vscale=1.7; }
  else if(s==2){ base=vec3(.88,.88,.90); vein=vec3(.27,.29,.33); sssT=vec3(.80,.70,.68); rough=.07; coat=.85; vmul=1.0; cloud=.12; vscale=1.0; }
  else { base=vec3(.022,.022,.026); vein=vec3(.88,.88,.90); sssT=vec3(.08,.08,.10); rough=.05; coat=.9; vmul=.7; cloud=.04; vscale=1.0; }
}

// marble vein field: returns x = vein mask 0..1, y = cloudy variation 0..1
vec2 veins(vec3 p, float warp, float style){
  vec3 q = p;
  q += warp*2.2*vec3(fbm(p*0.7), fbm(p*0.7+5.2), fbm(p*0.7+9.1)) - warp*1.1;
  if(style > 0.5 && style < 1.5) q *= vec3(1.0, 2.2, 1.0);          // bone: elongated fibres
  float n = fbm(q + 3.3);
  float r = 1.0 - abs(2.0*n - 1.0);
  float v = pow(r, style > 0.5 && style < 1.5 ? 6.0 : (style > 2.5 ? 22.0 : 11.0));
  float n2 = fbm(q*2.7 + 11.0);
  float r2 = 1.0 - abs(2.0*n2 - 1.0);
  v = max(v, pow(r2, 16.0)*0.55);
  float cloud = fbm(q*0.55 + 20.0);
  return vec2(v, cloud);
}

void main(){
  TDCheckDiscard();
  int style = int(uP0.x + 0.5);
  float gloss = uP0.y, sss = uP0.z, warp = uP0.w;
  float vAmt = uP1.x, vScale = uP1.y, cAmt = uP1.z, cScale = uP1.w;
  vec3 base, vein, sssT; float rough, coat, vmul, cloud, vsc;
  styleData(style, base, vein, sssT, rough, coat, vmul, cloud, vsc);

  vec3 p = vv.oP;
  vec3 N = normalize(vv.wN);
  vec3 V = normalize(vv.cam - vv.wP);
  if(dot(N,V) < 0.0) N = -N;

  // ---- veins ----
  vec2 vc = veins(p*vScale*vsc, warp, float(style));
  float vMask = sat(vc.x*vAmt*vmul);
  vec3 albedo = base*uTint.rgb;
  albedo = mix(albedo, albedo*(1.0 - cloud*1.2*(vc.y-0.35)), 0.55);          // cloudy mottling
  vec3 veinCol = vein*uVeinC.rgb;
  albedo = mix(albedo, veinCol, vMask);
  float veinSSS = 1.0 - 0.6*vMask;

  // ---- hairline cracks (voronoi edges), masked so only some edges appear ----
  float crack = 0.0, stain = 0.0;
  if(cAmt > 0.001){
    vec3 cp = p*cScale;
    cp += 0.35*vec3(vnoise(cp*1.7), vnoise(cp*1.7+4.1), vnoise(cp*1.7+8.3));   // wobble -> organic cracks
    float w = mix(0.004, 0.06, uP2.x);
    vec2 f = voro(cp);
    float e = f.y - f.x;
    float th = 0.82 - cAmt*0.6;
    float vis = smoothstep(th, th+0.10, fbm2(p*cScale*0.35 + 7.0));
    float c1 = (1.0 - smoothstep(0.0, w, e))*vis;
    vec2 f2 = voro(cp*2.9 + 5.0);
    float vis2 = smoothstep(th+0.12, th+0.28, fbm2(p*cScale*1.1 + 17.0));
    float c2 = (1.0 - smoothstep(0.0, w*0.7, f2.y - f2.x))*vis2*0.8;
    crack = max(c1, c2);
    stain = (1.0 - smoothstep(0.0, w*9.0, e))*vis*0.35;
  }
  albedo = mix(albedo, albedo*vec3(.80,.74,.62), stain);                      // grime wicking into the crack
  albedo = mix(albedo, albedo*0.05 + vec3(.012,.010,.008), crack);
  float rr = clamp(rough*mix(1.7, 0.55, gloss), 0.03, 1.0);
  rr = mix(rr, 0.7, crack);
  float cAmtCoat = coat*gloss*(1.0 - crack);

  // ---- diffuse with colored wrap lighting (fake subsurface) ----
  float wrap = 0.15 + sss*0.85;
  vec3 Nr = envRot()*N;
  vec3 diff = vec3(0.025,0.027,0.035)*(0.6+0.4*Nr.y);
  vec3 sssTint = sssT*sss;
  vec3 Ls[4] = vec3[4](L0,L1,L2,L3);
  vec3 Cs[4] = vec3[4](C0*0.30,C1*0.30,C2*0.22,C3*0.25);
  for(int i=0;i<4;i++){
    float ndl = dot(Nr, Ls[i]);
    float d = sat((ndl + wrap)/(1.0 + wrap));
    float band = exp(-pow(ndl/(0.28*wrap + 0.03), 2.0));      // reddish terminator band
    diff += Cs[i]*(albedo*d + sssTint*albedo*band*0.9*veinSSS);
  }
  diff *= uEnv.y*0.55;
  // thin-edge / back translucency: light glowing through at grazing angles and opposite the key light
  float NdV = sat(dot(N,V));
  float thick = mix(1.0, 0.35 + 0.65*fbm2(p*2.0 + 31.0), uP2.z);
  float back = pow(sat(dot(V, -normalize((envRot()*vec3(0.,0.,0.)) + (transpose(envRot())*L0) + N*0.35))), 3.0);
  float rimT = pow(1.0 - NdV, 3.0);
  diff += uEnv.y*sssTint*albedo*(back*1.3 + rimT*0.8)*thick*veinSSS*1.2;

  // ---- specular: satin base + glaze coat ----
  vec3 R = reflect(-V, N);
  vec3 F0 = vec3(0.04);
  vec3 specBase = studioEnv(R, rr)*envBRDF(F0, rr, NdV);
  float Fc = 0.04 + 0.96*pow(1.0 - NdV, 5.0);
  vec3 specCoat = studioEnv(R, 0.035)*Fc*cAmtCoat*1.0;
  vec3 col = diff*(1.0 - Fc*cAmtCoat) + specBase*(1.0 - Fc*cAmtCoat) + specCoat;
  oFragColor = TDOutputSwizzle(vec4(col, 1.0));
}
