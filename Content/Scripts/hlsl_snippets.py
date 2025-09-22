BLEND_AC_HLSL = r"""
// Angle-corrected normal blend in World Space
float3 BlendAC(float3 nA_ws, float3 nB_ws, float w) {
    nA_ws = normalize(nA_ws);
    nB_ws = normalize(nB_ws);
    float3 t = normalize(lerp(nA_ws, nB_ws, w));
    return t;
}
"""

HEIGHT_WEIGHT_HLSL = r"""
// Returns weight 0..1 based on relative height difference with contrast and balance
float HeightWeight(float hA, float hB, float contrast, float balance) {
    float b = saturate(balance);
    float off = (b * 2.0 - 1.0);
    float d = (hB - hA) + off;
    float w = smoothstep(-contrast, contrast, d);
    return saturate(w);
}
"""

ROTATE2D_HLSL = r"""
// Rotate UV around 0.5,0.5 by degrees
float2 Rotate2D(float2 uv, float deg){
    float rad = radians(deg);
    float2 c = float2(0.5,0.5);
    float s = sin(rad), co = cos(rad);
    float2 p = uv - c;
    float2 r = float2(p.x*co - p.y*s, p.x*s + p.y*co);
    return r + c;
}
"""

TRIPLANAR_HLSL = r"""
// Simple triplanar sampler. expects:
// TexObject2D Base, float3 WorldPos, float3 WorldNormal, float Tiling, float sharpness
// returns float4 rgba
float4 TriplanarSample(Texture2D Base, SamplerState SS, float3 WP, float3 NW, float tiling, float sharpness){
    float3 n = abs(normalize(NW));
    float3 w = pow(n, sharpness.xxx);
    w /= max(1e-5, (w.x + w.y + w.z));
    float2 uvX = WP.zy * tiling;
    float2 uvY = WP.xz * tiling;
    float2 uvZ = WP.xy * tiling;

    float4 sx = Base.Sample(SS, uvX);
    float4 sy = Base.Sample(SS, uvY);
    float4 sz = Base.Sample(SS, uvZ);

    return sx * w.x + sy * w.y + sz * w.z;
}
"""
