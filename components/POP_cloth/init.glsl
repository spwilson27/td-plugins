// Prepare cloth state on the input mesh. in0 = mesh (+ Pin attribute), in1 = Analyze POP (Min / Max of P).
// Writes: RestP (rest position), PrevP (previous position), Pin (1 = pinned).
uniform vec4 uI;   // x = pin mode (0 top row, 1 Pin attribute / group, 2 none), y = top-row thickness (fraction of height)
void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    vec3 p = TDIn_P();
    float pin = TDIn_Pin();
    int mode = int(uI.x + 0.5);
    if (mode == 0) {
        vec3 mx = TDIn_Max(1, 0);
        vec3 mn = TDIn_Min(1, 0);
        float h = max(mx.y - mn.y, 1e-6);
        pin = (p.y >= mx.y - uI.y * h - 1e-5) ? 1.0 : 0.0;
    } else if (mode == 2) {
        pin = 0.0;
    } else {
        pin = pin > 0.5 ? 1.0 : 0.0;
    }
    RestP[id] = p;
    PrevP[id] = p;
    Pin[id] = pin;
}
