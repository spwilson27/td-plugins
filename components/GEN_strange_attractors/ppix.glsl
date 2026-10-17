in vec3 vCol;
layout(location = 0) out vec4 fragColor;
void main(){ fragColor = TDOutputSwizzle(vec4(vCol, 1.0)); }
