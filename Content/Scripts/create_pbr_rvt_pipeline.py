# Run in Unreal Editor: Window -> Developer Tools -> Output Log -> `py Scripts/create_pbr_rvt_pipeline.py`
import json
import unreal
from pathlib import Path

# ---------------- Config ----------------
ROOT = "/Game/Materials/PBR_RVT"
MF_UV = f"{ROOT}/MF_UVBlock_PBR"
MF_RVT = f"{ROOT}/MF_RVT_Read"
MASTER_MAT = f"{ROOT}/M_PBR_Master"
MI_BASE = f"{ROOT}/MI_PBR_Base"
RVT_ASSET = f"{ROOT}/T_VT_PBR_Master"

CONFIG_PATH = Path(unreal.Paths.project_content_dir()) / "Config" / "naming.json"

# HLSL snippets
from Scripts.hlsl_snippets import BLEND_AC_HLSL, HEIGHT_WEIGHT_HLSL, ROTATE2D_HLSL, TRIPLANAR_HLSL

# -------------- Helpers -----------------
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_lib = unreal.MaterialEditingLibrary
ed_lib = unreal.EditorAssetLibrary

def ensure_folder(path):
    if not ed_lib.does_directory_exist(path):
        ed_lib.make_directory(path)

def create_material_function(path, desc=""):
    factory = unreal.MaterialFunctionFactoryNew()
    func = asset_tools.create_asset(Path(path).name, str(Path(path).parent).replace("\\","/"), unreal.MaterialFunction, factory)
    func.get_editor_property("description")
    func.set_editor_property("description", desc)
    return func

def create_material(path, domain=unreal.MaterialDomain.MD_SURFACE, shading=unreal.MaterialShadingModel.MSM_SUBSTRATE):
    # MSM_DEFAULT_LIT is typical; offering Substrate default for 5.6 flexibility. Change if needed.
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(Path(path).name, str(Path(path).parent).replace("\\","/"), unreal.Material, factory)
    mat.set_editor_property("material_domain", domain)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("use_material_attributes", True)
    mat_lib.recompile_material(mat)
    return mat

def add_comment(material, text, pos, size=(400,160), color=(0.1,0.1,0.1)):
    c = mat_lib.create_material_expression(material, unreal.MaterialExpressionComment, -1, -1)
    c.set_editor_property("size_x", size[0])
    c.set_editor_property("size_y", size[1])
    c.set_editor_property("text", text)
    c.set_editor_property("comment_color", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    c.set_editor_property("editable", True)
    c.material_expression_editor_x = pos[0]
    c.material_expression_editor_y = pos[1]
    return c

def add_param(material, klass, name, pos, default=None):
    node = mat_lib.create_material_expression(material, klass, pos[0], pos[1])
    node.set_editor_property("parameter_name", name)
    if default is not None:
        if isinstance(default, float) and hasattr(node, "default_value"):
            node.set_editor_property("default_value", default)
        elif isinstance(default, unreal.LinearColor) and hasattr(node, "default_value"):
            node.set_editor_property("default_value", default)
    return node

def connect(out_node, out_pin, in_node, in_prop):
    mat_lib.connect_material_expressions(out_node, out_pin, in_node, in_prop)

def create_runtime_virtual_texture(path):
    factory = unreal.RuntimeVirtualTextureFactory()
    rvt = asset_tools.create_asset(Path(path).name, str(Path(path).parent).replace("\\","/"), unreal.RuntimeVirtualTexture, factory)
    # Default config — tune as needed
    rvt.set_editor_property("virtual_texture_build_resolution", 1024)
    rvt.set_editor_property("tile_size", 128)
    rvt.set_editor_property("remove_low_mips", False)
    rvt.set_editor_property("material_type", unreal.RuntimeVirtualTextureMaterialType.BASE_COLOR_NORMAL_SPECULAR)
    rvt.set_editor_property("enable_compress_height", False)
    return rvt

# -------------- Build MF_UVBlock_PBR --------------
def build_mf_uv():
    func = create_material_function(MF_UV, "Unified UV & Triplanar block")
    graph = func.get_editor_property("expression_collection")

    # Function inputs
    in_scale = unreal.MaterialExpressionFunctionInput()
    in_scale.input_name = "UV_Scale"
    in_scale.input_type = unreal.FunctionInputType.SCALAR
    in_scale.preview_value = unreal.LinearColor(1,0,0,0)

    in_rot = unreal.MaterialExpressionFunctionInput()
    in_rot.input_name = "UV_RotateDeg"
    in_rot.input_type = unreal.FunctionInputType.SCALAR
    in_rot.preview_value = unreal.LinearColor(0,0,0,0)

    in_offset = unreal.MaterialExpressionFunctionInput()
    in_offset.input_name = "UV_Offset"
    in_offset.input_type = unreal.FunctionInputType.VECTOR2

    in_use_triplanar = unreal.MaterialExpressionFunctionInput()
    in_use_triplanar.input_name = "Use_Triplanar"
    in_use_triplanar.input_type = unreal.FunctionInputType.SCALAR

    in_triplanar_tiling = unreal.MaterialExpressionFunctionInput()
    in_triplanar_tiling.input_name = "Triplanar_Tiling"
    in_triplanar_tiling.input_type = unreal.FunctionInputType.SCALAR
    in_triplanar_tiling.preview_value = unreal.LinearColor(1,0,0,0)

    in_triplanar_sharp = unreal.MaterialExpressionFunctionInput()
    in_triplanar_sharp.input_name = "Triplanar_Sharpness"
    in_triplanar_sharp.input_type = unreal.FunctionInputType.SCALAR
    in_triplanar_sharp.preview_value = unreal.LinearColor(4,0,0,0)

    func.add_expression(in_scale)
    func.add_expression(in_rot)
    func.add_expression(in_offset)
    func.add_expression(in_use_triplanar)
    func.add_expression(in_triplanar_tiling)
    func.add_expression(in_triplanar_sharp)

    # Coordinates
    texcoord = unreal.MaterialExpressionTextureCoordinate()
    func.add_expression(texcoord)

    add = unreal.MaterialExpressionAdd()
    func.add_expression(add)
    add_const = unreal.MaterialExpressionConstant2Vector()
    add_const.constant_x = 0.0
    add_const.constant_y = 0.0
    func.add_expression(add_const)
    add.a = texcoord
    add.b = add_const

    mult = unreal.MaterialExpressionMultiply()
    func.add_expression(mult)
    mult.a = add
    mult.b = in_scale

    # Rotate Custom
    rotate_node = unreal.MaterialExpressionCustom()
    rotate_node.code = ROTATE2D_HLSL + "\nreturn Rotate2D(Input0, Input1);"
    rotate_node.output_type = unreal.CustomMaterialOutputType.CMOT_FLOAT2
    rotate_node.set_editor_property("inputs", [
        unreal.CustomInput(input_name="Input0", input=mult),
        unreal.CustomInput(input_name="Input1", input=in_rot),
    ])
    func.add_expression(rotate_node)

    # Offset
    add_off = unreal.MaterialExpressionAdd()
    func.add_expression(add_off)
    add_off.a = rotate_node
    add_off.b = in_offset

    # World data for triplanar
    wpos = unreal.MaterialExpressionWorldPosition()
    func.add_expression(wpos)
    wnorm = unreal.MaterialExpressionPixelNormalWS()
    func.add_expression(wnorm)

    # Outputs
    out_uv = unreal.MaterialExpressionFunctionOutput()
    out_uv.output_name = "UV_Main"
    out_uv.a = add_off
    func.add_expression(out_uv)

    out_wp = unreal.MaterialExpressionFunctionOutput()
    out_wp.output_name = "WorldPos"
    out_wp.a = wpos
    func.add_expression(out_wp)

    out_wn = unreal.MaterialExpressionFunctionOutput()
    out_wn.output_name = "WorldNormal"
    out_wn.a = wnorm
    func.add_expression(out_wn)

    # Triplanar HLSL kept in MF_RVT_Read for sampling, we only provide coords/weights here

    func.post_edit_change()
    func.mark_package_dirty()
    unreal.MaterialEditingLibrary.recompile_material_function(func)
    return func

# -------------- Build MF_RVT_Read --------------
def build_mf_rvt():
    func = create_material_function(MF_RVT, "RVT Sample & Blend helpers")
    # Inputs
    fin_rvt = unreal.MaterialExpressionFunctionInput()
    fin_rvt.input_name = "RVT_Asset"
    fin_rvt.input_type = unreal.FunctionInputType.SAMPLER
    func.add_expression(fin_rvt)

    fin_uv = unreal.MaterialExpressionFunctionInput()
    fin_uv.input_name = "UV"
    fin_uv.input_type = unreal.FunctionInputType.VECTOR2
    func.add_expression(fin_uv)

    fin_mip = unreal.MaterialExpressionFunctionInput()
    fin_mip.input_name = "MipBias"
    fin_mip.input_type = unreal.FunctionInputType.SCALAR
    func.add_expression(fin_mip)

    # RuntimeVirtualTextureSample
    rvt_sample = unreal.MaterialExpressionRuntimeVirtualTextureSample()
    rvt_sample.mip_value_mode = unreal.TextureMipValueMode.TMVM_MIPBIAS
    func.add_expression(rvt_sample)
    rvt_sample.coordinates = fin_uv
    rvt_sample.mip_value = fin_mip
    rvt_sample.virtual_texture = None  # bound via parameter in material

    # Outputs
    fout_bc = unreal.MaterialExpressionFunctionOutput()
    fout_bc.output_name = "BaseColor"
    fout_bc.a = rvt_sample.rgb
    func.add_expression(fout_bc)

    fout_a = unreal.MaterialExpressionFunctionOutput()
    fout_a.output_name = "Alpha"
    fout_a.a = rvt_sample.a
    func.add_expression(fout_a)

    fout_n = unreal.MaterialExpressionFunctionOutput()
    fout_n.output_name = "NormalWS"
    # RVT normal output pin is in tangent or world based on RVT type; we treat as world.
    fout_n.a = rvt_sample.world_normal
    func.add_expression(fout_n)

    fout_r = unreal.MaterialExpressionFunctionOutput()
    fout_r.output_name = "Roughness"
    fout_r.a = rvt_sample.roughness
    func.add_expression(fout_r)

    fout_m = unreal.MaterialExpressionFunctionOutput()
    fout_m.output_name = "Metallic"
    fout_m.a = rvt_sample.metallic
    func.add_expression(fout_m)

    fout_h = unreal.MaterialExpressionFunctionOutput()
    fout_h.output_name = "Height"
    fout_h.a = rvt_sample.world_height
    func.add_expression(fout_h)

    func.post_edit_change()
    func.mark_package_dirty()
    unreal.MaterialEditingLibrary.recompile_material_function(func)
    return func

# -------------- Build Master Material --------------
def build_master():
    mat = create_material(MASTER_MAT)

    # Comment blocks
    add_comment(mat, "[UV Block]", (-3600, -800), (600, 240))
    add_comment(mat, "[Local PBR]", (-2800, -800), (800, 600))
    add_comment(mat, "[RVT Read]", (-1800, -800), (700, 600))
    add_comment(mat, "[RVT Write]", (-900, -800), (700, 600))
    add_comment(mat, "[Layer Mix]", (-200, -800), (700, 600))
    add_comment(mat, "[Debug]", (700, -800), (600, 300))

    # Parameters
    uv_scale = add_param(mat, unreal.MaterialExpressionScalarParameter, "UV_Scale", (-3500, -750), 1.0)
    uv_rot = add_param(mat, unreal.MaterialExpressionScalarParameter, "UV_RotateDeg", (-3500, -650), 0.0)
    uv_off = mat_lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -3500, -550)
    uv_off.set_editor_property("parameter_name", "UV_Offset")
    uv_off.default_value = unreal.LinearColor(0,0,0,0)

    use_triplanar = add_param(mat, unreal.MaterialExpressionStaticBoolParameter, "Use_Triplanar", (-3500, -450))
    tri_tiling = add_param(mat, unreal.MaterialExpressionScalarParameter, "Triplanar_Tiling", (-3500, -350), 1.0)
    tri_sharp = add_param(mat, unreal.MaterialExpressionScalarParameter, "Triplanar_Sharpness", (-3500, -250), 4.0)

    base_tex = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -2700, -750)
    base_tex.set_editor_property("parameter_name", "BaseColor_Tex")
    norm_tex = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -2700, -650)
    norm_tex.set_editor_property("parameter_name", "Normal_Tex")
    orm_tex = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -2700, -550)
    orm_tex.set_editor_property("parameter_name", "ORM_Tex")
    height_tex = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -2700, -450)
    height_tex.set_editor_property("parameter_name", "Height_Tex")

    rvt_param = mat_lib.create_material_expression(mat, unreal.MaterialExpressionRuntimeVirtualTextureParameter, -1700, -750)
    rvt_param.set_editor_property("parameter_name", "RVT_PBR_Target")

    use_rvt_read = add_param(mat, unreal.MaterialExpressionStaticBoolParameter, "Use_RVT_Read", (-1700, -350))
    use_rvt_write = add_param(mat, unreal.MaterialExpressionStaticBoolParameter, "Use_RVT_Write", (-900, -350))
    use_height_blend = add_param(mat, unreal.MaterialExpressionStaticBoolParameter, "Use_HeightBlend", (-200, -350))

    r_override = add_param(mat, unreal.MaterialExpressionScalarParameter, "Roughness_Override", (-2600, -100), -1.0)
    m_override = add_param(mat, unreal.MaterialExpressionScalarParameter, "Metallic_Override", (-2600, -40), -1.0)
    ao_mult = add_param(mat, unreal.MaterialExpressionScalarParameter, "AO_Mult", (-2600, 20), 1.0)
    rvt_mip = add_param(mat, unreal.MaterialExpressionScalarParameter, "RVT_MipBias", (-1700, -250), 0.0)

    dbg_show = add_param(mat, unreal.MaterialExpressionStaticBoolParameter, "Debug_ShowRVT", (700, -750))
    dbg_mip = add_param(mat, unreal.MaterialExpressionScalarParameter, "Debug_RVT_MipBias", (700, -650), 0.0)
    dbg_weight_vis = add_param(mat, unreal.MaterialExpressionScalarParameter, "Debug_WeightVis", (700, -550), 0.0)

    # MF_UVBlock_PBR call
    mf_uv = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, -3200, -750)
    mf_uv.set_editor_property("material_function", unreal.load_object(None, MF_UV))
    mat_lib.connect_material_expressions(uv_scale, "", mf_uv, "UV_Scale")
    mat_lib.connect_material_expressions(uv_rot, "", mf_uv, "UV_RotateDeg")
    mat_lib.connect_material_expressions(uv_off, "", mf_uv, "UV_Offset")
    mat_lib.connect_material_expressions(use_triplanar, "", mf_uv, "Use_Triplanar")
    mat_lib.connect_material_expressions(tri_tiling, "", mf_uv, "Triplanar_Tiling")
    mat_lib.connect_material_expressions(tri_sharp, "", mf_uv, "Triplanar_Sharpness")

    # Local sampling (feature switch fallback)
    samp_base = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -2400, -750)
    samp_base.texture_object = base_tex
    connect(mf_uv, "UV_Main", samp_base, "UVs")

    samp_norm = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -2400, -650)
    samp_norm.texture_object = norm_tex
    samp_norm.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    connect(mf_uv, "UV_Main", samp_norm, "UVs")

    samp_orm = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -2400, -550)
    samp_orm.texture_object = orm_tex
    connect(mf_uv, "UV_Main", samp_orm, "UVs")

    samp_height = mat_lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -2400, -450)
    samp_height.texture_object = height_tex
    connect(mf_uv, "UV_Main", samp_height, "UVs")

    # Unpack ORM
    ao = mat_lib.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -2200, -550)
    ao.r = True; ao.g = False; ao.b = False; ao.a = False
    ao.input = samp_orm
    rough = mat_lib.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -2200, -520)
    rough.g = True; rough.input = samp_orm
    metal = mat_lib.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -2200, -490)
    metal.b = True; metal.input = samp_orm

    # Overrides (if override >= 0)
    r_cmp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionIf, -2100, -120)
    r_cmp.a = r_override; r_cmp.b = rough; r_cmp.c = r_override; r_cmp.agreaterthanb = r_override; r_cmp.alessthanb = rough
    m_cmp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionIf, -2100, -60)
    m_cmp.a = m_override; m_cmp.b = metal; m_cmp.c = m_override; m_cmp.agreaterthanb = m_override; m_cmp.alessthanb = metal
    ao_mul = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -2100, 20)
    ao_mul.a = ao; ao_mul.b = ao_mult

    # MF_RVT_Read call
    mf_rvt = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, -1500, -750)
    mf_rvt.set_editor_property("material_function", unreal.load_object(None, MF_RVT))
    mat_lib.connect_material_expressions(rvt_param, "", mf_rvt, "RVT_Asset")
    mat_lib.connect_material_expressions(mf_uv, "UV_Main", mf_rvt, "UV")
    mat_lib.connect_material_expressions(rvt_mip, "", mf_rvt, "MipBias")

    # Weight sources
    vcol = mat_lib.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -1200, -350)
    slope_dot = mat_lib.create_material_expression(mat, unreal.MaterialExpressionDotProduct, -1200, -250)
    slope_dot.a = mat_lib.create_material_expression(mat, unreal.MaterialExpressionPixelNormalWS, -1300, -260)
    up = mat_lib.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -1300, -210)
    up.constant = unreal.LinearColor(0,0,1,1)
    slope_dot.b = up
    slope_mask = mat_lib.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -1100, -250)
    slope_mask.input = mat_lib.create_material_expression(mat, unreal.MaterialExpressionAbs, -1150, -250)
    slope_mask.input.input = slope_dot

    # Height weight custom
    height_custom = mat_lib.create_material_expression(mat, unreal.MaterialExpressionCustom, -200, -600)
    height_custom.code = HEIGHT_WEIGHT_HLSL + "\nreturn HeightWeight(Input0, Input1, Input2, Input3);"
    height_custom.output_type = unreal.CustomMaterialOutputType.CMOT_FLOAT1
    height_custom.inputs = [
        unreal.CustomInput(input_name="Input0", input=samp_height),     # Local height
        unreal.CustomInput(input_name="Input1", input=mf_rvt),          # RVT Height output wired later
        unreal.CustomInput(input_name="Input2", input=add_param(mat, unreal.MaterialExpressionScalarParameter, "Height_Contrast", (-200, -680), 0.2)),
        unreal.CustomInput(input_name="Input3", input=add_param(mat, unreal.MaterialExpressionScalarParameter, "Height_Balance", (-200, -640), 0.5)),
    ]

    # Extract RVT outputs for connections
    rvt_bc = mat_lib.create_material_expression(mat, unreal.MaterialExpressionFunctionOutput, -1400, -730)  # dummy to hold pin names
    # Not necessary to place; using function call output pins directly below.

    # Weight combine: base on VertexColor.R, mod by slope
    w_mul = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -900, -250)
    w_mul.a = vcol
    w_mul.b = slope_mask

    # Final weight: choose height or mask via switch
    w_lerp_selector = mat_lib.create_material_expression(mat, unreal.MaterialExpressionStaticSwitch, -200, -520)
    w_lerp_selector.a = w_mul
    w_lerp_selector.b = height_custom
    w_lerp_selector.value = use_height_blend

    # Normal blend (Custom)
    blend_ac = mat_lib.create_material_expression(mat, unreal.MaterialExpressionCustom, -100, -300)
    blend_ac.code = BLEND_AC_HLSL + "\nreturn BlendAC(Input0, Input1, Input2);"
    blend_ac.output_type = unreal.CustomMaterialOutputType.CMOT_FLOAT3
    blend_ac.inputs = [
        unreal.CustomInput(input_name="Input0", input=mat_lib.create_material_expression(mat, unreal.MaterialExpressionTransform, -1500, -640))
    ]
    # Transform local tangent-space normal to world space
    trans = blend_ac.inputs[0].input
    trans.transform_source_type = unreal.MaterialVectorCoordTransformSource.TANGENT
    trans.transform_type = unreal.MaterialVectorCoordTransformType.WORLD
    trans.input = samp_norm

    # Connect RVT normal
    blend_ac.inputs.append(unreal.CustomInput(input_name="Input1", input=mf_rvt))
    # Weight
    blend_ac.inputs.append(unreal.CustomInput(input_name="Input2", input=w_lerp_selector))

    # Color/rough/met blend
    bc_lerp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 50, -750)
    bc_lerp.a = samp_base
    bc_lerp.b = mf_rvt
    bc_lerp.alpha = w_lerp_selector

    r_lerp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 50, -700)
    r_lerp.a = r_cmp
    r_lerp.b = mf_rvt
    r_lerp.alpha = w_lerp_selector

    m_lerp = mat_lib.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 50, -650)
    m_lerp.a = m_cmp
    m_lerp.b = mf_rvt
    m_lerp.alpha = w_lerp_selector

    ao_min = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMin, 50, -600)
    ao_min.a = ao_mul
    ao_min.b = mat_lib.create_material_expression(mat, unreal.MaterialExpressionConstant, 40, -590)  # default if RVT lacks AO
    ao_min.b.r = 1.0

    # Make Material Attributes
    make = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMakeMaterialAttributes, 350, -750)
    make.base_color = bc_lerp
    make.normal = blend_ac
    make.roughness = r_lerp
    make.metallic = m_lerp
    make.ambient_occlusion = ao_min

    # Debug: Show RVT
    debug_switch = mat_lib.create_material_expression(mat, unreal.MaterialExpressionStaticSwitch, 900, -740)
    debug_switch.value = dbg_show
    debug_switch.a = make
    debug_switch.b = mat_lib.create_material_expression(mat, unreal.MaterialExpressionMakeMaterialAttributes, 900, -680)
    debug_bc = mat_lib.create_material_expression(mat, unreal.MaterialExpressionAppendVector, 900, -640)
    debug_bc.a = mf_rvt
    debug_bc.b = mf_rvt  # duplicate to make 3 channels if needed

    # Output to material
    mat.set_editor_property("use_material_attributes", True)
    mat.material_attributes = debug_switch

    # RVT Write
    rvt_out = mat_lib.create_material_expression(mat, unreal.MaterialExpressionRuntimeVirtualTextureOutput, -600, -750)
    # BaseColor -> from make.base_color
    rvt_out.base_color = bc_lerp
    rvt_out.specular = None  # unused
    rvt_out.roughness = r_lerp
    rvt_out.metallic = m_lerp
    rvt_out.world_height = samp_height
    # Normal requires WS; transform already in blend_ac result
    rvt_out.world_normal = blend_ac

    mat_lib.recompile_material(mat)
    return mat

# -------------- Build MI --------------
def build_mi_base():
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = asset_tools.create_asset(Path(MI_BASE).name, str(Path(MI_BASE).parent).replace("\\","/"), unreal.MaterialInstanceConstant, factory)
    mi.set_editor_property("parent", unreal.load_object(None, MASTER_MAT))
    unreal.EditorAssetLibrary.save_asset(MI_BASE)
    return mi

# -------------- Create RVT asset --------------
def build_rvt_asset():
    rvt = create_runtime_virtual_texture(RVT_ASSET)
    unreal.EditorAssetLibrary.save_asset(RVT_ASSET)
    return rvt

def main():
    # Load naming config if exists
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        global ROOT, MF_UV, MF_RVT, MASTER_MAT, MI_BASE, RVT_ASSET
        ROOT = data.get("root", ROOT)
        MF_UV = f"{ROOT}/{data.get('mf_uv', 'MF_UVBlock_PBR')}"
        MF_RVT = f"{ROOT}/{data.get('mf_rvt', 'MF_RVT_Read')}"
        MASTER_MAT = f"{ROOT}/{data.get('master', 'M_PBR_Master')}"
        MI_BASE = f"{ROOT}/{data.get('mi_base', 'MI_PBR_Base')}"
        RVT_ASSET = f"{ROOT}/{data.get('rvt', 'T_VT_PBR_Master')}"

    ensure_folder(ROOT)
    mf1 = build_mf_uv()
    mf2 = build_mf_rvt()
    mat = build_master()
    mi = build_mi_base()
    rvt = build_rvt_asset()
    print("PBR RVT pipeline created:")
    print(f" - {MF_UV}")
    print(f" - {MF_RVT}")
    print(f" - {MASTER_MAT}")
    print(f" - {MI_BASE}")
    print(f" - {RVT_ASSET}")

if __name__ == "__main__":
    main()
