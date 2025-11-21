# Camera Angle
# Copyright (C) 2025 VGmove
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
	"name": "Camera Angle",
	"author": "VGmove",
	"version": (1, 0, 0),
	"blender": (4, 1, 0),
	"location": "Properties > Camera > Camera Angle",
	"description": "Addon for quick setup of the orthographic camera angle",
	"category": "Camera",
}

import bpy
import math
from bpy.props import IntProperty, FloatProperty, EnumProperty, PointerProperty
from mathutils import Vector

# Handlers properties
class CameraAngleHandlers:
	@staticmethod
	def update_projection_type(self, context):
		if not context.object or context.object.type != 'CAMERA':
			return
		CameraAngleManager.update_camera_position(context.object)

	@staticmethod
	def update_slider_horizontal(self, context):
		if not context.object or context.object.type != 'CAMERA':
			return
		CameraAngleManager.update_camera_position(context.object)

	@staticmethod
	def update_slider_vertical(self, context):
		if not context.object or context.object.type != 'CAMERA':
			return
		CameraAngleManager.update_camera_position(context.object)

	@staticmethod
	def update_distance(self, context):
		if not context.object or context.object.type != 'CAMERA':
			return
		CameraAngleManager.update_camera_position(context.object)

# Properties
class CameraAngleProperties(bpy.types.PropertyGroup):
	slider_horizontal: IntProperty(
		name="",
		description="Horizontal Camera Views",
		min=1,
		max=8,
		default=2,
		update=CameraAngleHandlers.update_slider_horizontal
	)

	slider_vertical: IntProperty(
		name="", 
		description="Vertical Camera Views",
		min=1,
		max=5,
		default=2,
		update=CameraAngleHandlers.update_slider_vertical
	)

	distance: FloatProperty(
		name="",
		description="Distance from target object",
		min=0.1,
		max=5,
		default=1,
		update=CameraAngleHandlers.update_distance
	)

	projection_type: EnumProperty(
		name="Projection Type",
		description="Type of projection",
		items=[
			('ISOMETRIC', "Isometric", "Isometric projection (35.264°)"),
			('TRIMETRIC', "Trimetric", "Trimetric projection (+20°)"),
			('DIMETRIC', "Dimetric", "Dimetric projection (45°)")
		],
		default='ISOMETRIC',
		update=CameraAngleHandlers.update_projection_type
	)

class CameraAngleManager:
	@staticmethod
	def get_camera_target(camera_obj):
		target_base_name = f"{camera_obj.name}_Target"
		
		camera_obj.data.type = 'ORTHO'
		camera_obj.lock_location = [True, True, True]
		camera_obj.lock_rotation = [True, True, True]
		camera_obj.lock_scale = [True, True, True]

		# Check parent object
		if camera_obj.parent and camera_obj.parent.type == 'EMPTY':
			target_obj = camera_obj.parent
			target_obj.lock_rotation = [True, True, True]
			target_obj.lock_scale = [True, True, True]
			target_obj.rotation_euler = (0.0, 0.0, 0.0)
			return target_obj

		# If no parent object, create target object
		camera_obj.data.ortho_scale = 1
		
		camera_world_matrix = camera_obj.matrix_world.copy()
		
		target_obj = bpy.data.objects.new(target_base_name, None)
		target_obj.empty_display_type = 'ARROWS'
		target_obj.empty_display_size = 0.1
		target_obj.show_name = True
		target_obj.show_in_front = True
		target_obj.lock_rotation = [True, True, True]
		target_obj.lock_scale = [True, True, True]
		target_obj.rotation_euler = (0.0, 0.0, 0.0)
		
		# Set target object position forward camera
		camera_direction = camera_world_matrix.to_quaternion() @ Vector((0, 0, -1))
		target_obj.location = camera_world_matrix.translation + camera_direction * camera_obj.data.property.distance
		
		for collection in camera_obj.users_collection:
			collection.objects.link(target_obj)
		
		current_parent = camera_obj.parent
		current_matrix_parent_inverse = camera_obj.matrix_parent_inverse.copy()
		if current_parent:
			target_obj.parent = current_parent
			target_obj.matrix_parent_inverse = current_parent.matrix_world.inverted()
		
		camera_obj.parent = target_obj
		camera_obj.matrix_parent_inverse = target_obj.matrix_world.inverted()
		camera_obj.matrix_world = camera_world_matrix

		return target_obj

	@staticmethod
	def update_camera_position(camera_obj):
		target_obj = CameraAngleManager.get_camera_target(camera_obj)

		camera_props = camera_obj.data.property
		
		horizontal = camera_props.slider_horizontal
		vertical = camera_props.slider_vertical
		distance = camera_props.distance
		projection_type = camera_props.projection_type
		
		old_target_world_pos = target_obj.matrix_world.translation.copy()
		target_obj.rotation_euler = (0.0, 0.0, 0.0)
		bpy.context.view_layer.update()
		
		target_world_pos = target_obj.matrix_world.translation.copy()
		
		if projection_type == 'ISOMETRIC':
			horizontal_angle = math.radians((horizontal - 1) * 45)
			vertical_angles = [89.95, 35.264, 0, -35.264, -89.95]
		elif projection_type == 'DIMETRIC':
			horizontal_angle = math.radians((horizontal - 1) * 45)
			vertical_angles = [89.95, 15, 0, -15, -89.95]
		elif projection_type == 'TRIMETRIC':
			if (horizontal - 1) % 2 == 1:
				horizontal_angle = math.radians(((horizontal - 1) * 45) + 30)
			else:
				horizontal_angle = math.radians(((horizontal - 1) * 45) + 15)
			vertical_angles = [89.95, 45, 0, -45, -89.95]

		if 1 <= vertical <= 5:
			vertical_angle_rad = math.radians(vertical_angles[vertical - 1])

			# World position camera
			x = distance * math.cos(vertical_angle_rad) * math.cos(horizontal_angle)
			y = distance * math.cos(vertical_angle_rad) * math.sin(horizontal_angle)
			z = distance * math.sin(vertical_angle_rad)
			
			# set world position camera
			camera_world_pos = target_world_pos + Vector((x, y, z))
			camera_obj.location = camera_world_pos
		
		direction = target_world_pos - camera_obj.location
		if direction.length > 0:
			rot_quat = direction.to_track_quat('-Z', 'Y')
			camera_obj.rotation_euler = rot_quat.to_euler()
		
		camera_obj.matrix_parent_inverse = target_obj.matrix_world.inverted()

class CAMERA_OT_create_target(bpy.types.Operator):
	bl_idname = "camera.create_target"
	bl_label = "Create Camera Target"
	bl_description = "Create target object for camera"
	
	def execute(self, context):
		if context.object and context.object.type == 'CAMERA':
			CameraAngleManager.update_camera_position(context.object)
			self.report({'INFO'}, "Camera target created")
		else:
			self.report({'ERROR'}, "Select a camera first")
		return {'FINISHED'}

class DATA_PT_camera_angle_panel(bpy.types.Panel):
	bl_label = "Camera Angle"
	bl_idname = "DATA_PT_camera_angle_panel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"

	@classmethod
	def poll(cls, context):
		return context.object and context.object.type == 'CAMERA'

	def draw(self, context):
		camera_obj = context.object
		layout = self.layout

		if not camera_obj.parent or not camera_obj.parent.type == 'EMPTY':
			col = layout.column()
			box = col.box()
			box.alert = False
			row = box.row()
			row.label(text="No Camera Target")
			row.operator(CAMERA_OT_create_target.bl_idname, text="Create")
		else:
			col = layout.column()

			camera_data = camera_obj.data
			camera_props = camera_data.property

			row = col.row()
			split = row.split(factor=0.39)
			split.alignment = 'RIGHT'
			split.label(text="Projection")
			split.prop(camera_props, "projection_type", text="")

			row = col.row()
			split = row.split(factor=0.39)
			split.alignment = 'RIGHT'
			split.label(text="Horizontal")
			split.prop(camera_props, "slider_horizontal", text="")

			row = col.row()
			split = row.split(factor=0.39)
			split.alignment = 'RIGHT'
			split.label(text="Vertical")
			split.prop(camera_props, "slider_vertical", text="")

			row = col.row()
			split = row.split(factor=0.39)
			split.alignment = 'RIGHT'
			split.label(text="Distance")
			split.prop(camera_props, "distance", text="")

classes = (
	CameraAngleProperties,
	CAMERA_OT_create_target,
	DATA_PT_camera_angle_panel
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Camera.property = PointerProperty(type=CameraAngleProperties)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	
	del bpy.types.Camera.property

if __name__ == "__main__":
	register()