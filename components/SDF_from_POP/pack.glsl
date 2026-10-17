// SDF_from_POP / points: pack the input points into one attribute buffer
//   pts[i] = (x, y, z, radius, r, g, b, 0); radius < 0 marks a point that is skipped (beyond Maxpoints, or radius <= 0).
// HAS_PSCALE / HAS_COLOR are #defined above this line when the input carries PointScale / Color.
// uA = (Radius, use PointScale, Maxpoints, use Color attribute); uC = (default colour rgb)
void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    vec3 p = TDIn_P();
    float r = uA.x;
#ifdef HAS_PSCALE
    if (uA.y > 0.5) r *= TDIn_PointScale();
#endif
    vec3 c = uC.rgb;
#ifdef HAS_COLOR
    if (uA.w > 0.5) c = TDIn_Color().rgb;
#endif
    if (float(id) >= uA.z || !(r > 0.0)) r = -1.0;
    pts[id][0] = p.x; pts[id][1] = p.y; pts[id][2] = p.z; pts[id][3] = r;
    pts[id][4] = c.r; pts[id][5] = c.g; pts[id][6] = c.b; pts[id][7] = 0.0;
}
