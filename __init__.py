# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "GTA V Model importer",
    "author" : "Lendo Keilbaum",
    "description" : "Import GTA V models (.odr, .odd)",
    "location": "File > Import",
    "blender" : (2, 80, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "Not for commercial use!",
    "category" : "Import"
}

if "bpy" in locals():
    import importlib
    if "importer" in locals():
        importlib.reload(importer)
else:
    from . import importer



import bpy
import os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        axis_conversion,
        )



class ImportGTA(bpy.types.Operator, ImportHelper):

    bl_idname = "import_scene.gta"
    bl_label = 'Import mesh'
    bl_options = {'UNDO'}
    filename_ext = [".odr", ".odd"]

    filter_glob: StringProperty(
            default="*.odr;*.odd",
            options={'HIDDEN'}
            )

    import_armature: EnumProperty(
        name="import armature",
        description="Auto will use existing armature or create new one. Selecting the armature before importing the mesh, can solve name conflicts.",
        items=[
            ("no", "no", "no armature", 1),
            ("create", "create", "force armature creation", 2),
            ("auto", "auto", "armature can be reused", 3),
        ],
        default="auto",
        options=set()
    )

    create_materials: EnumProperty(
        name="create materials",
        description="Auto will use existing material or create new one.",
            items=[
            ("no", "no", "no materials", 1),
            ("create", "create", "force material creation", 2),
            ("auto", "auto", "materials can be reused", 3),
        ],
        default="auto",
        options=set()
    )

    texture_format: EnumProperty(
        name="texture format",
        description="choose format of the textures",
            items=[
            (".dds", ".dds", ".dds", 1),
            (".png", ".png", ".png", 2),
            (".bmp", ".bmp", ".bmp", 3),
            (".jpeg", ".jpeg", ".jpeg", 4),
        ],
        default=".dds",
        options=set()
    )

    LOD: EnumProperty(
        name="LOD",
        description="If LOD does not exist, closest match will be loaded",
        items=[
            ("High", "High", "High", 1),
            ("Med", "Med", "Med", 2),
            ("Low", "Low", "Low", 3),
            ("Vlow", "Vlow", "Vlow", 4),
        ],
        default="High",
        options=set()
    )

    def execute(self, context):
        keywords = self.as_keywords()
        keywords["name"] = os.path.basename(keywords["filepath"]).split(".")[0]
        keywords["file_extension"] = os.path.basename(keywords["filepath"]).split(".")[1]
        keywords["folder"] = os.path.dirname(keywords["filepath"])
        return importer.load(self, context, **keywords)

# Add to a menu
def menu_func_import(self, context):
    self.layout.operator(ImportGTA.bl_idname, text="GTA V Model (.odr/.odd)")


def register():
    bpy.utils.register_class(ImportGTA)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportGTA)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()