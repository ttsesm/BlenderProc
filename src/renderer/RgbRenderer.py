import bpy

from src.renderer.RendererInterface import RendererInterface
from src.utility.Utility import Utility


class RgbRenderer(RendererInterface):
    """ Renders rgb images for each registered keypoint.

    Images are stored as PNG-files or JPEG-files with 8bit color depth.
    .. csv-table::
        :header: "Parameter", "Description"

        "render_texture_less", "Render all objects with a white slightly glossy texture, does not change emission "
                                "materials, Type: bool. Default: False."
        "image_type", "Image type of saved rendered images, Type: str. Default: 'PNG'. Available: ['PNG','JPEG']"
        "transparent_background", "Whether to render the background as transparent or not, Type: bool. Default: False."
    """
    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._image_type = config.get_string('image_type', 'PNG')

    def change_to_texture_less_render(self):
        """
        Changes the materials, which do not contain a emission shader to a white slightly glossy texture
        :return:
        """
        new_mat = bpy.data.materials.new(name="TextureLess")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")

        # setting the color values for the shader
        principled_bsdf.inputs['Specular'].default_value = 0.65  # specular
        principled_bsdf.inputs['Roughness'].default_value = 0.2  # roughness

        for object in [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]:
            # replace all materials with the new texture less material
            for slot in object.material_slots:
                emission_shader = False
                # check if the material contains an emission shader:
                for node in slot.material.node_tree.nodes:
                    # check if one of the shader nodes is a Emission Shader
                    if 'Emission' in node.bl_idname:
                        emission_shader = True
                        break
                # only replace materials, which do not contain any emission shader
                if not emission_shader:
                    if self._use_alpha_channel:
                        slot.material = self.add_alpha_texture_node(slot.material, new_mat)
                    else:
                        slot.material = new_mat

    def run(self):
        # if the rendering is not performed -> it is probably the debug case.
        do_undo = not self._avoid_rendering
        with Utility.UndoAfterExecution(perform_undo_op=do_undo):
            self._configure_renderer(use_denoiser=True, default_denoiser="Intel")

            # In case a previous renderer changed these settings
            #Store as RGB by default unless the user specifies store_alpha as true in yaml
            bpy.context.scene.render.image_settings.color_mode = "RGBA" if self.config.get_bool("transparent_background", False) else "RGB"
            #set the background as transparent if transparent_background is true in yaml
            bpy.context.scene.render.film_transparent = self.config.get_bool("transparent_background", False)
            bpy.context.scene.render.image_settings.file_format = self._image_type
            bpy.context.scene.render.image_settings.color_depth = "8"

            # only influences jpg quality
            bpy.context.scene.render.image_settings.quality = 95

            # check if texture less render mode is active
            if self._texture_less_mode:
                self.change_to_texture_less_render()

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            self._render("rgb_")

        if self._image_type == 'PNG':
            self._register_output("rgb_", "colors", ".png", "1.0.0")
        elif self._image_type == 'JPEG':
            self._register_output("rgb_", "colors", ".jpg", "1.0.0")
        else:
            raise Exception("Unknown Image Type " + self._image_type)
