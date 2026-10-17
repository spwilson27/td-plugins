flat in float vDep;
layout(location = 0) out vec4 fragColor;
void main(){
    fragColor = TDOutputSwizzle(vec4(vDep, 0.0, 0.0, 1.0));
}
