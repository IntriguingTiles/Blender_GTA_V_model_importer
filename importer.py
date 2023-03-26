if "bpy" in locals():
    import importlib
    importlib.reload(file_parser)
else:
    from . import file_parser

import bpy
import os
from mathutils import (Vector, Quaternion, Matrix, Euler)

bone_mapping = []
skeleton = None
selection = None
vertexStructures = {
    "N209731BE": {"pos": 0, "normal": 1, "color": 2, "uv": 3},
    "N51263BB5": {"pos": 0, "normal": 1, "color": 2, "uv": 3, "undef2": 4},
    "S9445853F": {"pos": 0, "weights": 1, "bone_indices": 2, "normal": 3, "color": 4, "uv": 5, "undef2": 6},
    "S12D0183F": {"pos": 0, "weights": 1, "bone_indices": 2, "normal": 3, "color": 4, "undef1": 5, "uv": 6, "uv2": 7, "undef2": 8},
    "SD7D22350": {"pos": 0, "weights": 1, "bone_indices": 2, "normal": 3, "color": 4, "undef1": 5, "uv": 6, "undef2": 7},
    "SBED48839": {"pos": 0, "weights": 1, "bone_indices": 2, "normal": 3, "color": 4, "undef1": 5, "uv": 6},
    "NC794193B": {"pos": 0, "normal": 1, "color": 2, "bone_indices": 3, "uv": 4, "uv2": 5, "undef1": 6},
    "S1E9F420D": {"pos": 0, "weights": 1, "bone_indices": 2, "normal": 3, "color": 4, "uv": 5}

}

def getNameFromFile(filepath):
    return os.path.basename(filepath).split(".")[0]


def find_in_folder(folder, file_name=None, extension=None):
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            # print(os.path.join(root, file))
            if extension:
                if file.endswith(extension):
                    return os.path.join(root, file)
            else:
                if file.endswith(file_name):
                    return os.path.join(root, file)
    return None


def getMaterial(shaders, shader_index, mesh_name, create_materials, **kwargs):

    def getShaderNode(mat):
        shader_node = node_out.inputs['Surface'].links[0].from_node
        return shader_node

    def getShaderInput(mat, name):
        shaderNode = getShaderNode(mat)
        return shaderNode.inputs[name]

    def getSampler(sampler_name, **kwargs):
        dot_split = sampler_name.split(".")
        if len(dot_split) > 1:
            sampler_name = dot_split[0]
        image_name = sampler_name.lower()
        image_file = image_name + kwargs["texture_format"]
        split = image_name.split("\\")
        image_path = ""
        path_variants = []

        if not "givemechecker" in image_name and not "*null*" in image_name:
            if len(split) > 1:
                image_name = split[1]
                path_variants.append(os.path.join(kwargs["texture_folder"], split[0], image_name + kwargs["texture_format"]))
                path_variants.append(os.path.join(kwargs["texture_folder"], image_name + kwargs["texture_format"]))
                path_variants.append(os.path.join(kwargs["texture_folder"], os.path.pardir, split[0], image_name + kwargs["texture_format"]))
            else:
                path_variants.append(os.path.join(kwargs["texture_folder"], image_file))
                path_variants.append(os.path.join(kwargs["texture_folder"], os.path.pardir, image_file))
                path_variants.append(os.path.join(kwargs["texture_folder"], os.path.pardir, image_name, image_file))

            for path in path_variants:
                if os.path.exists(path):
                    image_path = path
                    break
            if not image_path:
                image_path = find_in_folder(kwargs["folder"], file_name=image_name + kwargs["texture_format"])

            if image_path:
                teximage_node = ntree.nodes.new('ShaderNodeTexImage')
                img = bpy.data.images.load(image_path, check_existing=True)
                img.name = kwargs["name"]+ "_" + image_name
                teximage_node.image = img
                return teximage_node
            else:
                print('sampler not found! "{0}"'.format(path_variants))
                return None
        else:
            print("no sampler to assign!")

    # Get material
    mat_name = kwargs["name"]+ "_" + mesh_name + str(shader_index)
    mat = bpy.data.materials.get(mat_name)

    if mat is None or create_materials == "create":
        # create material
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        ntree = mat.node_tree
        node_out = ntree.get_output_node('EEVEE')
        shader = getShaderNode(mat)
        links = ntree.links
        # add diffuse map
        colorInput = getShaderInput(mat, 'Base Color')
        if "DiffuseSampler" in shaders["members"][shader_index]:
            teximage_node = getSampler(shaders["members"][shader_index]["DiffuseSampler"], **kwargs)
            if teximage_node:
                teximage_node.interpolation = 'Smart'

                # blend mode
                # mat.blend_method = 'CLIP'
                # mat.shadow_method = 'CLIP'

                links.new(teximage_node.outputs['Color'],colorInput)
                links.new(teximage_node.outputs[1], shader.inputs["Alpha"])


        # add normal map
        if "BumpSampler" in shaders["members"][shader_index]:
            teximage_node = getSampler(shaders["members"][shader_index]["BumpSampler"], **kwargs)
            if teximage_node:
                teximage_node.interpolation = 'Smart'
                normalMap_node = ntree.nodes.new('ShaderNodeNormalMap')
                if shaders["members"][shader_index]["Bumpiness"]:
                    normalMap_node.inputs[0].default_value = float(shaders["members"][shader_index]["Bumpiness"])

                teximage_node.image.colorspace_settings.name = 'Raw'

                # invert greenchannel
                seperateRGB = ntree.nodes.new("ShaderNodeSeparateRGB")
                links.new(teximage_node.outputs['Color'], seperateRGB.inputs[0])

                invertNode = ntree.nodes.new("ShaderNodeInvert")
                links.new(seperateRGB.outputs[1], invertNode.inputs[1])
                combineRGB = ntree.nodes.new("ShaderNodeCombineRGB")
                links.new(invertNode.outputs[0], combineRGB.inputs[1])
                links.new(seperateRGB.outputs[0], combineRGB.inputs[0])
                links.new(seperateRGB.outputs[2], combineRGB.inputs[2])

                links.new(combineRGB.outputs[0], normalMap_node.inputs['Color'])
                links.new(normalMap_node.outputs['Normal'], shader.inputs['Normal'])

        # add specular map
        if "SpecSampler" in shaders["members"][shader_index]:
            teximage_node = getSampler(shaders["members"][shader_index]["SpecSampler"], **kwargs)
            if teximage_node:
                teximage_node.interpolation = 'Smart'
                seperateRGB = ntree.nodes.new("ShaderNodeSeparateRGB")
                links.new(teximage_node.outputs['Color'], seperateRGB.inputs[0])
                links.new(seperateRGB.outputs[2], shader.inputs[5])



    return mat


def setVertexAttributes(Obj, mesh, VertexData, VertexDeclaration, skinned):
    global bone_mapping
    mesh.uv_layers.new(name="UVMap")
    uvlayer = mesh.uv_layers.active.data
    mesh.calc_loop_triangles()
    normals = []
    vcolor1 = None
    vcolor2 = None
    vcolor3 = None
    # get vertex mapping
    normalIndex = vertexStructures[VertexDeclaration]["normal"]
    uvIndex = vertexStructures[VertexDeclaration]["uv"]
    if skinned:
        boneIndex = vertexStructures[VertexDeclaration]["bone_indices"]
        weightIndex = vertexStructures[VertexDeclaration]["weights"]
    if "color" in vertexStructures[VertexDeclaration]:
        vcolor1 = mesh.vertex_colors.new(name="color1")
    if "undef1" in vertexStructures[VertexDeclaration]:
        vcolor2 = mesh.vertex_colors.new(name="color2")
    if "undef2" in vertexStructures[VertexDeclaration]:
        vcolor3 = mesh.vertex_colors.new(name="color3")

    for i, lt in enumerate(mesh.loop_triangles):
        for loop_index in lt.loops:
            # set uv coordinates
            uvlayer[loop_index].uv = VertexData[mesh.loops[loop_index].vertex_index][uvIndex]
            # flip y axis
            uvlayer[loop_index].uv[1] = 1 - uvlayer[loop_index].uv[1]
            # set normals (1)
            normals.append(VertexData[mesh.loops[loop_index].vertex_index][normalIndex])
            # add bone weights
            if skinned:
                # bone indices (4)
                for i, vg in enumerate(VertexData[mesh.loops[loop_index].vertex_index][boneIndex]):
                    vg_name = bone_mapping[int(vg)]
                    if not vg_name in Obj.vertex_groups:
                        group = Obj.vertex_groups.new(name=vg_name)
                    else:
                        group = Obj.vertex_groups[vg_name]
                    # bone weights (3)
                    weight = VertexData[mesh.loops[loop_index].vertex_index][weightIndex][i]
                    if weight > 0.0:
                        group.add([mesh.loops[loop_index].vertex_index], weight, 'REPLACE' )
            if vcolor1:
                vcolor1.data[loop_index].color = VertexData[mesh.loops[loop_index].vertex_index][vertexStructures[VertexDeclaration]["color"]]/256
            if vcolor2:
                vcolor2.data[loop_index].color = VertexData[mesh.loops[loop_index].vertex_index][vertexStructures[VertexDeclaration]["undef1"]]/256
            if vcolor3:
                vcolor3.data[loop_index].color = VertexData[mesh.loops[loop_index].vertex_index][vertexStructures[VertexDeclaration]["undef2"]]

    # normal custom verts
    mesh.use_auto_smooth = True
    mesh.normals_split_custom_set(normals)



def findArmature(skel_file):
    # try to get the existing armature by name
    global skeleton, bone_mapping, selection
    skel_name = os.path.basename(skel_file).split(".")[0]

    def findArmatureFromList(objectList):
        global skeleton
        for obj in objectList:
            if skel_name in obj.name and obj.type == 'ARMATURE':
                skeleton = obj
                for bone in skeleton.pose.bones:
                    bone_mapping.append(bone.name)
                return True
        return False

    # first check selection
    if not findArmatureFromList(selection):
        # then all objects
        return findArmatureFromList(bpy.data.objects)
    else:
        return True


def importMesh(filepath, shaders, import_armature, skinned=False, create_materials=False, **kwargs):
    global skeleton, bone_mapping
    p = file_parser.GTA_Parser()
    p.read_file(filepath)
    base_name = getNameFromFile(filepath)

    objects = []
    for num, geometry in enumerate(p.data["members"][0]["members"][1]["members"]):
        name = base_name + str(num)
        faces = geometry["members"][0]["faces"]
        verts = geometry["members"][1]["positions"]
        shader_index = int(geometry["ShaderIndex"])
        skinned_mesh = p.data["members"][0]["Skinned"] == "True" and import_armature != "no"
        bone_count = int(p.data["members"][0]["BoneCount"])

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, (), faces)

        # find skelton
        root = None
        if "odd_root" in kwargs:
            root = kwargs["odd_root"]
        elif "odr_root" in kwargs:
            root = kwargs["odr_root"]
        if skinned_mesh and not skeleton and root:
            skel_file = find_in_folder(root, extension=".skel")
            if skel_file:
                if import_armature == "create" or not findArmature(skel_file):
                    loadSkeleton(skel_file, **kwargs)
            if not skeleton:
                skinned_mesh = False
                print("no skeleton file or armature found for: {0}".format(filepath))

        if not mesh.validate(verbose=True):
            VertexDeclaration = geometry["VertexDeclaration"]
            Obj = bpy.data.objects.new(name, mesh)
            setVertexAttributes(Obj, mesh, geometry["members"][1]["vertices"], VertexDeclaration, skinned_mesh)
            bpy.context.scene.collection.objects.link(Obj)
            Obj.select_set(True)
            objects.append(Obj)
            bpy.context.view_layer.objects.active = Obj
            if create_materials != "no":
                # Assign material to object
                mat = getMaterial(shaders, shader_index, base_name, create_materials, **kwargs)
                Obj.data.materials.append(mat)
        else:
            print('mesh validation failed for: "{0}"'.format(name))

    if bpy.context.view_layer.objects.active:
        # join all submeshes
        if len(objects) > 1:
            bpy.ops.object.join()

        bpy.context.view_layer.objects.active.name = base_name
        activeObject = bpy.context.view_layer.objects.active

        # apply armature modifier
        if skinned_mesh and skeleton and activeObject:
            mod = activeObject.modifiers.new("armature", 'ARMATURE')
            if mod:
                mod.object = skeleton
                activeObject.parent = skeleton

        activeObject.select_set(False)
        return activeObject
    else:
        return None


def buildArmature(skel_file):
    arma = bpy.data.armatures.new(os.path.basename(skel_file.name))
    Obj = bpy.data.objects.new(os.path.basename(skel_file.name), arma)
    bpy.context.scene.collection.objects.link(Obj)
    bpy.context.view_layer.objects.active = Obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    numBones = skel_file.data["members"][0]["NumBones"]

    def addBone(bone, armature, obj, parent=None):
        global bone_mapping

        bone_name = bone["attributes"][0]
        bone_mapping.append(bone_name)
        b_bone = armature.edit_bones.new(bone_name)
        b_bone.head = (0,0,0)
        b_bone.tail = (0,0.05,0)
        b_bone.use_inherit_rotation = True
        b_bone.use_local_location = True
        quad = Quaternion((float(bone["RotationQuaternion"][3]), float(bone["RotationQuaternion"][0]),
            float(bone["RotationQuaternion"][1]), float(bone["RotationQuaternion"][2])))
        # quad = Quaternion(map(float, bone["RotationQuaternion"]))
        mat = quad.to_matrix().to_4x4()
        b_bone.matrix = mat
        position = Vector(map(float, bone["LocalOffset"]))
        b_bone.translate(position)
        if parent:
            b_bone.parent = parent
            b_bone.matrix = parent.matrix @ b_bone.matrix

        # add child bones
        for children in bone["members"]:
            for child in children["members"]:
                addBone(child, armature, obj, b_bone)

    addBone(skel_file.data["members"][0]["members"][0], arma, Obj)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    return Obj


def loadSkeleton(filepath, **kwargs):
    global skeleton
    skel_file = file_parser.GTA_Parser()
    if skel_file.read_file(filepath):
        skeleton = buildArmature(skel_file)
        return True
    else:
        # print(filepath)
        print("skel file not found")
        return False


def loadODR(filepath, import_armature, **kwargs):
    global skeleton
    kwargs["odr_root"] = os.path.dirname(filepath)
    kwargs["odr_name"] = os.path.basename(filepath).split(".")[0]
    odrFile = file_parser.GTA_Parser()
    odrFile.read_file(filepath)
    name = getNameFromFile(filepath)
    lodgroup = odrFile.getMemberByName("LodGroup")
    shaders = odrFile.getMemberByName("Shaders")
    skel = odrFile.getMemberByName("Skeleton")

    # check for odr skeleton
    if skel != "null" and import_armature != "no" and not skeleton:
        if not isinstance(skel, str):
            skel = " ".join(skel)
        kwargs["odr_skeleton_path"] = os.path.join(kwargs["folder"], *skel.split("\\"))
        if os.path.exists(kwargs["odr_skeleton_path"]):
            if import_armature == "create" or not findArmature(kwargs["odr_skeleton_path"]):
                loadSkeleton(kwargs["odr_skeleton_path"], **kwargs)
        else:
            print("missing odr skeleton file: {0}".format(kwargs["odr_skeleton_path"]))

    mesh_path = ""
    # get LOD
    LODs = []
    match = False
    if not "texture_folder" in kwargs:
        p1 = os.path.join(kwargs["odr_root"], kwargs["odr_name"])
        if os.path.exists(p1):
            kwargs["texture_folder"] = p1


    for mesh in lodgroup["members"]:
        for key, value in mesh.items():
            if name in key and key.endswith(".mesh"):
                path = os.path.join(kwargs["folder"], *key.split("\\"))
                LODs.append(path)
                if kwargs["LOD"] == mesh["name"]:
                    match = True
                    mesh_path = path

    # if no match take lowest LOD
    if not match:
        print("LOD not found, take lowest available")
        mesh_path = LODs[-1]

    return importMesh(mesh_path, shaders, import_armature, **kwargs)


def loadODD(filepath, import_armature, **kwargs):
    kwargs["odd_root"] = os.path.dirname(filepath)
    kwargs["odd_name"] = os.path.basename(filepath).split(".")[0]
    oddFile = file_parser.GTA_Parser()
    oddFile.read_file(filepath)
    root = oddFile.getMemberByName("Version")
    mesh_list = []
    base_path = kwargs["folder"]

    # check for odd skeleton
    if import_armature != "no":
        kwargs["odd_skeleton_path"] = os.path.join(kwargs["odd_root"], kwargs["odd_name"], kwargs["odd_name"] + ".skel")
        if os.path.exists(kwargs["odd_skeleton_path"]):
            if import_armature == "create" or not findArmature(kwargs["odd_skeleton_path"]):
                loadSkeleton(kwargs["odd_skeleton_path"], **kwargs)

    for odr in root["values"]:
        odr_path = os.path.join(base_path, *odr.split("\\"))
        kwargs["folder"] = os.path.dirname(odr_path)
        kwargs["texture_folder"] = os.path.dirname(odr_path)
        mesh_list.append(loadODR(odr_path, import_armature, **kwargs))
    return mesh_list


def deselectAll():
    for obj in bpy.data.objects:
        obj.select_set(False)


def load(operator, context, filepath="", import_armature=False, **kwargs):
    global bone_mapping, skeleton, selection
    skeleton = None
    bone_mapping = []

    def message(self, context):
        self.layout.label(text="failed to import model!")

    selection = bpy.context.selected_objects
    deselectAll()
    bpy.context.view_layer.objects.active = None

    if kwargs["file_extension"] == "odr":
        meshObjects = [loadODR(filepath, import_armature, **kwargs)]
    if kwargs["file_extension"] == "odd":
        meshObjects = loadODD(filepath, import_armature, **kwargs)


    if not meshObjects:
        bpy.context.window_manager.popup_menu(message, title="Error", icon='ERROR')
    return {'FINISHED'}