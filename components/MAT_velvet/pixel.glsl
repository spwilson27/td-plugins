// mat_velvet: Charlie/Ashikhmin-style sheen + rim fuzz, optional shell fur (instanced shells). Object-space, no UVs.
uniform vec4 uV0; // x=mode (0 sheen, 1 shells), y=shells, z=fur length, w=strand density
uniform vec4 uV1; // x=fuzz roughness, y=sheen strength, z=rim fuzz, w=fiber noise
uniform vec4 uV2; // x=strand width, y=root darkness, z=pile patches, w=unused
uniform vec4 uBase;  // rgb base
uniform vec4 uSheenC; // rgb sheen

out vec4 oFragColor;

vec2 hash22(vec2 p){ vec3 p3 = fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)); p3 += dot(p3,p3.yzx+33.33); return fract((p3.xx+p3.yz)*p3.zy); }
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx)*.1031); p3 += dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }

// Charlie distribution (Estevez & Kulla) + Neubelt visibility
float charlieD(float rough, float NdH){
  float inv = 1.0/max(rough,0.05);
  float s2 = max(1.0 - NdH*NdH, 0.0001);
  return (2.0 + inv)*pow(s2, inv*0.5)/(2.0*PI);
}
float neubeltV(float NdL, float NdV){ return 1.0/(4.0*max(NdL + NdV - NdL*NdV, 0.12)); }

void main(){
  TDCheckDiscard();
  bool shells = uV0.x > 0.5;
  float h = shells ? vv.sh : 0.0;
  float furLen = uV0.z;
  vec3 p = vv.oP;
  vec3 N = normalize(vv.wN);
  vec3 V = normalize(vv.cam - vv.wP);
  float strandRnd = 0.5, tipFade = 0.0;
  if(shells){
    // strand cells: project on dominant object axis (hair-like columns), jittered
    vec3 an = abs(normalize(vv.oN));
    vec2 uv = (an.x>an.y && an.x>an.z) ? p.yz + 7.1 : ((an.y>an.z) ? p.xz + 3.7 : p.xy + 1.3);
    vec2 g = uv*uV0.w; vec2 id = floor(g); vec2 f = fract(g) - 0.5;
    vec2 off = (hash22(id) - 0.5)*0.55;
    strandRnd = hash12(id + 17.0);
    float len = mix(0.45, 1.0, strandRnd);
    float rad = 0.5*uV2.x*(1.0 - h/len);
    // slight per-strand bend along height so strands are not perfectly straight columns
    vec2 bend = (hash22(id+3.0)-0.5)*h*0.8;
    float d = length(f - off - bend);
    if(h > 0.0 && (h > len || d > rad)) discard;
    tipFade = h/len;
  }
  // pile patches: brushed / crushed areas change the sheen response
  float pileP = fbm2(p*2.5 + 11.0);
  float patchMod = 1.0 + uV2.z*(pileP - 0.5)*1.4;
  float fiber = vnoise(p*260.0);
  float fiberMod = 1.0 - uV1.w*0.55*fiber;

  float NdV = sat(dot(N,V));
  float ao = shells ? mix(1.0 - uV2.y, 1.0, pow(h, 0.7)) : 1.0;
  vec3 base = uBase.rgb*(shells ? mix(0.85, 1.15, strandRnd) : 1.0);
  // forward scattering darkens facing areas of the pile; grazing areas light up
  vec3 albedo = base*mix(1.0, 0.45, NdV*NdV);

  vec3 Nr = envRot()*N;
  vec3 diff = vec3(0.02,0.022,0.03);
  vec3 Ls[4] = vec3[4](L0,L1,L2,L3);
  vec3 Cs[4] = vec3[4](C0,C1,C2,C3);
  vec3 sheen = vec3(0.0);
  float rough = clamp(uV1.x, 0.1, 1.0);
  for(int i=0;i<4;i++){
    vec3 Lw = transpose(envRot())*Ls[i];
    float ndl = sat(dot(N, Lw));
    float wrapd = sat((dot(Nr, Ls[i]) + 0.5)/1.5);
    diff += Cs[i]*0.26*wrapd;
    vec3 H = normalize(Lw + V);
    float NdH = sat(dot(N,H));
    // sheen is allowed to wrap a little past the terminator
    float ndlw = sat((dot(N,Lw)+0.35)/1.35);
    sheen += Cs[i]*charlieD(rough, NdH)*neubeltV(ndl, NdV)*ndlw;
  }
  diff *= uEnv.y; sheen *= uEnv.y;
  vec3 col = albedo*diff*0.55*ao;
  col += uSheenC.rgb*sheen*uV1.y*0.6*patchMod*fiberMod*mix(1.0, 0.5 + 0.5*ao, 0.8);
  // rim fuzz: soft lit halo at grazing angles
  float rim = pow(1.0 - NdV, 2.6);
  vec3 envL = diffuseLight(N, 0.6);
  col += uSheenC.rgb*envL*rim*uV1.z*1.6*patchMod*mix(1.0, 0.6+0.4*ao, 0.8) + uSheenC.rgb*studioEnv(reflect(-V,N), 0.95)*rim*uV1.z*0.5;
  if(shells) col *= mix(1.0, 1.0 + 0.5*tipFade, 0.6);
  oFragColor = TDOutputSwizzle(vec4(col, 1.0));
}
