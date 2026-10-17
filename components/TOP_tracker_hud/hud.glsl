// tracker_hud pass B: grid, boxes, connecting lines, procedural 5x7 pixel-font labels, scanlines
uniform vec4 uA; // ph, points, labelmode(0 id,1 coords,2 both), fontsize px
uniform vec4 uB; // linecount, gridsize px, mix, scanlines
uniform vec4 uC; // boxsize px, labelcolor(0 red,1 white), linealpha, gridalpha
uniform vec4 uD; // dim input, unused
out vec4 fragColor;
#define MAXP 64
// 5x7 glyph rows (5 bits each) for chars: 0-9, '.', '/', ' ', '-'
const int FONT[14*7] = int[](
 14,17,19,21,25,17,14,   4,12,4,4,4,4,14,   14,17,1,2,4,8,31,   31,2,4,2,1,17,14,   2,6,10,18,31,2,2,
 31,16,30,1,1,17,14,     6,8,16,30,17,17,14, 31,1,2,4,8,8,8,    14,17,17,14,17,17,14, 14,17,17,15,1,2,12,
 0,0,0,0,0,12,12,        1,1,2,4,8,16,16,    0,0,0,0,0,0,0,     0,0,0,31,0,0,0);
float glyph(int code, ivec2 g){ // g: x 0..4, y 0..6 (0 = top row)
  if(g.x<0||g.x>4||g.y<0||g.y>6||code<0||code>13) return 0.;
  int row=FONT[code*7+g.y];
  return float((row>>(4-g.x))&1);
}
int ipow10(int k){ int r=1; for(int i=0;i<k;i++) r*=10; return r; }
// char code for a number field "%7.2f" given v = int(x*100)
int numChar(int v,int col){
  if(col==4) return 10;
  int k = col<4 ? 5-col : 6-col;       // col0->10^5 ... col3->10^2 ; col5->10^1, col6->10^0
  if(col==5) k=1; if(col==6) k=0;
  if(k>2 && v<ipow10(k)) return 12;
  return (v/ipow10(k))%10;
}
int labelChar(int line,int col,float idn,vec2 pxPos,int mode){
  int ln=line; if(mode==0) ln=0; else if(mode==1) ln=1;
  if(ln==0){ // id: 5 digits
    if(col<0||col>4) return 12;
    int v=int(idn); return (v/ipow10(4-col))%10;
  }
  // coords line "%7.2f / %7.2f"
  if(col<0||col>16) return 12;
  if(col<7) return numChar(int(pxPos.x*100.),col);
  if(col==8) return 11;
  if(col>=10) return numChar(int(pxPos.y*100.),col-10);
  return 12;
}
float seg(vec2 p,vec2 a,vec2 b){ vec2 pa=p-a,ba=b-a; float t=clamp(dot(pa,ba)/dot(ba,ba),0.,1.); return length(pa-ba*t); }
void main(){
  vec2 res=uTDOutputInfo.res.zw;
  vec2 uv=vUV.st; vec2 px=uv*res;
  vec3 src=texture(sTD2DInputs[0],uv).rgb*uC.w*0.+texture(sTD2DInputs[0],uv).rgb*uD.x;
  vec3 hud=vec3(0.); float a=0.;
  vec3 white=vec3(.93,.92,.88), red=vec3(1.,.08,.06);
  vec3 lc=uC.y<.5?red:white;
  // grid
  float gs=max(uB.y,8.);
  vec2 gp=mod(px,gs);
  float gl=(1.-smoothstep(0.,1.,min(gp.x,gs-gp.x)))+(1.-smoothstep(0.,1.,min(gp.y,gs-gp.y)));
  hud+=white*clamp(gl,0.,1.)*.10*uC.w; a+=.10*uC.w*clamp(gl,0.,1.);
  // crosses at intersections and edge ticks
  vec2 cp=(gp-gs*.5)*0.; vec2 d2=min(gp,gs-gp);
  float cross=(1.-step(1.,min(d2.x,d2.y)))*step(max(d2.x,d2.y),4.);
  hud+=white*cross*.5*uC.w;
  float tk=step(abs(px.x-floor(px.x/(gs*.25)+.5)*gs*.25),.7)*step(px.y,8.)+step(abs(px.y-floor(px.y/(gs*.25)+.5)*gs*.25),.7)*step(px.x,8.);
  hud+=white*tk*.7;
  int N=int(uA.y+.5);
  float fs=max(floor(uA.w/7.+.5),1.);
  float bh=uC.x*.5;
  // lines
  int LC=int(uB.x+.5);
  float ll=0.;
  for(int k=0;k<MAXP;k++){
    if(k>=LC||k>=N) break;
    int j=(k*5+3)%max(N,1); if(j==k) j=(k+1)%max(N,1);
    vec4 A=texelFetch(sTD2DInputs[1],ivec2(k,0),0), B=texelFetch(sTD2DInputs[1],ivec2(j,0),0);
    if(A.w<.5||B.w<.5) continue;
    float dl=seg(px,A.xy*res,B.xy*res);
    ll=max(ll,1.-smoothstep(.5,1.3,dl));
  }
  hud+=white*ll*uC.z; a=max(a,ll*uC.z);
  // points: boxes + labels
  float bx=0., tx=0.;
  for(int i=0;i<MAXP;i++){
    if(i>=N) break;
    vec4 P=texelFetch(sTD2DInputs[1],ivec2(i,0),0);
    if(P.w<.5) continue;
    vec2 pp=P.xy*res;
    vec2 q=px-pp;
    float dd=max(abs(q.x),abs(q.y))-bh;
    bx=max(bx,(1.-smoothstep(.4,1.2,abs(dd)))*step(abs(q.x),bh+2.)*step(abs(q.y),bh+2.));
    // label rect
    int mode=int(uA.z+.5);
    int nlines=mode==2?2:1;
    float cw=6.*fs, chh=8.*fs;
    vec2 o=pp+vec2(bh+6.,bh+2.);            // top-left of the text block (y up)
    vec2 r=vec2(px.x-o.x,o.y-px.y);
    if(r.x>=0.&&r.y>=0.&&r.x<17.*cw&&r.y<float(nlines)*chh){
      int line=int(r.y/chh); float ly=r.y-float(line)*chh;
      int col=int(r.x/cw); float lx=r.x-float(col)*cw;
      int code=labelChar(line,col,P.z,pp,mode==2?line:mode);
      if(code!=12){ ivec2 g=ivec2(int(lx/fs),int(ly/fs)); tx=max(tx,glyph(code,g)); }
    }
  }
  hud=mix(hud,white,bx); a=max(a,bx);
  hud=mix(hud,lc,tx); a=max(a,tx);
  vec3 col=src+hud*uB.z*(1.+0.*a);
  // scanlines
  float sc=.5+.5*sin(px.y*3.14159265);
  col*=1.-uB.w*.35*sc;
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
