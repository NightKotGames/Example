# PBR + RVT Master Pipeline

## Install
1. Enable Virtual Texture Support: Edit → Project Settings → Rendering → Virtual Textures.
2. Copy `Scripts`, `Config`, `Docs` to your Content root (or keep paths consistent).
3. In Editor: Window → Developer Tools → Output Log
   - py Scripts/create_pbr_rvt_pipeline.py

Assets created:
- MF_UVBlock_PBR, MF_RVT_Read, M_PBR_Master, MI_PBR_Base, T_VT_PBR_Master

## Use
- Place Runtime Virtual Texture Volume in level and assign T_VT_PBR_Master.
- To write RVT: in any mesh/material instance, toggle Use_RVT_Write and set RVT_PBR_Target to T_VT_PBR_Master; optionally enable Hide Primitives.
- To read RVT: toggle Use_RVT_Read; tune RVT_MipBias (+0.25..+0.75 for distance).
- Weighting:
  - VertexColor.R as mask, modulated by slope. Toggle Use_HeightBlend to drive by height vs RVT height.
- Overrides:
  - Roughness_Override / Metallic_Override: set >= 0 to force value; < 0 uses texture ORM.
- Debug:
  - Debug_ShowRVT shows RVT pass-through.

## Notes
- ORM layout: R=AO, G=Roughness, B=Metallic.
- Height map is optional but recommended for HeightBlend.
- For landscapes/roads: write BaseColor/Normal/Height; foliage/props: read only (grounding).
