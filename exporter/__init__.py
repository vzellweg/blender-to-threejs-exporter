# This file initializes the plugin and registers the export operator.


bl_info = {
    "name": "Blender to Three.js Exporter",
    "author": "Your Name",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "File > Export > Geometry Nodes to Three.js (.js)",
    "description": "Exports Geometry Nodes network to three.js JavaScript code",
    "category": "Import-Export",
}

import bpy
from .exporter import ExportGeometryNodesToThreeJS

def menu_func_export(self, context):
    self.layout.operator(ExportGeometryNodesToThreeJS.bl_idname, text="Geometry Nodes to Three.js (.js)")

def register():
    bpy.utils.register_class(ExportGeometryNodesToThreeJS)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportGeometryNodesToThreeJS)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
