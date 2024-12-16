# This is the core of the plugin, handling the export logic.


import bpy
import os
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
from .node_mappings import NODE_TYPE_MAPPING

class ExportGeometryNodesToThreeJS(bpy.types.Operator, ExportHelper):
    """Export Geometry Nodes to Three.js JavaScript Code"""
    bl_idname = "export_scene.geometry_nodes_to_threejs"
    bl_label = "Export Geometry Nodes to Three.js"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".js"
    filter_glob: StringProperty(
        default="*.js",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        obj = context.active_object

        if obj is None:
            self.report({'ERROR'}, "No active object found.")
            return {'CANCELLED'}

        # Find Geometry Nodes modifier
        geo_mod = None
        for mod in obj.modifiers:
            if mod.type == 'NODES':
                geo_mod = mod
                break

        if geo_mod is None:
            self.report({'ERROR'}, "Active object has no Geometry Nodes modifier.")
            return {'CANCELLED'}

        node_group = geo_mod.node_group
        node_data = self.traverse_node_tree(node_group)
        js_code = self.generate_threejs_code(node_data)

        # Write to file
        try:
            with open(self.filepath, 'w') as f:
                f.write(js_code)
            self.report({'INFO'}, f"Exported to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write file: {str(e)}")
            return {'CANCELLED'}

    def traverse_node_tree(self, node_group):
        nodes = node_group.nodes
        links = node_group.links

        node_data = {}

        for node in nodes:
            node_info = {
                'type': node.type,
                'name': node.name,
                'inputs': {},
                'outputs': {}
            }

            # Collect input connections
            for input in node.inputs:
                if input.is_linked:
                    link = input.links[0]
                    node_info['inputs'][input.name] = {
                        'from_node': link.from_node.name,
                        'from_socket': link.from_socket.name
                    }
                else:
                    # Store default value if not connected
                    node_info['inputs'][input.name] = input.default_value

            # Collect output connections
            node_info['outputs'] = {}
            for output in node.outputs:
                node_info['outputs'][output.name] = []
                for link in output.links:
                    node_info['outputs'][output.name].append({
                        'to_node': link.to_node.name,
                        'to_socket': link.to_socket.name
                    })

            node_data[node.name] = node_info

        return node_data

    def generate_threejs_code(self, node_data):
        code_lines = []
        code_lines.append("// Auto-generated by Blender to Three.js Exporter")
        code_lines.append("import * as THREE from 'three';")
        code_lines.append("")

        # Define nodes
        for node_name, info in node_data.items():
            node_type = info['type']
            threejs_class = NODE_TYPE_MAPPING.get(node_type, None)
            if threejs_class is None:
                code_lines.append(f"// Unsupported node type: {node_type} ({node_name})")
                continue

            # Prepare parameters
            params = {}
            for input_name, input_value in info['inputs'].items():
                if isinstance(input_value, dict):
                    # Connected input; handled via connections later
                    continue
                else:
                    params[input_name] = input_value

            # Generate parameter string
            params_str = ", ".join([f"{k}: {repr(v)}" for k, v in params.items()])
            code_lines.append(f"const {node_name} = new {threejs_class}({{{params_str}}});")

        code_lines.append("")

        # Connect nodes
        code_lines.append("// Connect Nodes")
        for node_name, info in node_data.items():
            node_type = info['type']
            threejs_class = NODE_TYPE_MAPPING.get(node_type, None)
            if threejs_class is None:
                continue

            for input_name, input_value in info['inputs'].items():
                if isinstance(input_value, dict):
                    from_node = input_value['from_node']
                    from_socket = input_value['from_socket']
                    # Assuming 'connectInput' is a method to link nodes
                    code_lines.append(f"{node_name}.connectInput('{input_name}', {from_node}, '{from_socket}');")

        code_lines.append("")

        # Compute nodes (assuming compute methods are defined)
        code_lines.append("// Compute Nodes")
        for node_name, info in node_data.items():
            node_type = info['type']
            threejs_class = NODE_TYPE_MAPPING.get(node_type, None)
            if threejs_class is None:
                continue
            code_lines.append(f"{node_name}.compute();")

        code_lines.append("")

        # Assuming there is an output node named 'Group Output'
        output_node_name = None
        for name, info in node_data.items():
            if info['type'] == 'GROUP_OUTPUT':
                output_node_name = name
                break

        if output_node_name:
            code_lines.append("// Get Final Geometry")
            code_lines.append(f"const finalGeometry = {output_node_name}.getOutput();")
            code_lines.append("")

            # Create mesh and add to scene
            code_lines.append("// Create Mesh and Add to Scene")
            code_lines.append("const scene = new THREE.Scene();")
            code_lines.append("const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });")
            code_lines.append("const mesh = new THREE.Mesh(finalGeometry, material);")
            code_lines.append("scene.add(mesh);")
        else:
            code_lines.append("// No Group Output node found.")

        return "\n".join(code_lines)