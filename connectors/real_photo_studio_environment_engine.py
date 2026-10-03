"""
Real Photo Studio Environment Engine.
Encapsulates high-end real photo studio background environments analyzed from top Pinterest fashion editorials (@derosa_finds aesthetic).

Trained Studio Environments:
1. CLEAN_CYCLORAMA_INFINITY_STUDIO: Off-white seamless cyclorama wall, soft ambient floor shadow fill, polished studio floor.
2. CRIMSON_RED_NEON_GRID_STUDIO: Red neon LED grid tiled wall, high-contrast Y2K streetwear edge lighting & top softbox.
3. GOLDEN_HOUR_MINIMALIST_STUDIO: Sand beige plaster wall, sun-dappled window shadows, potted olive tree branch.
4. KOREAN_ARCHWAY_CUBE_STUDIO: Off-white studio archway alcove with white cube seating block & warm floor lamp glow.
5. URBAN_CONCRETE_STREET_STUDIO: Textured grey concrete wall, natural open-shade street daylight & subtle shadows.
6. HIGH_KEY_CATALOG_STUDIO: Neutral off-white seamless paper backdrop, shadowless softbox lighting for fashion editorials.
7. NIGHT_FLASH_STAIRS_STUDIO: Nighttime urban concrete stairs with direct hard camera flash photography.
"""
from __future__ import annotations

import random
from typing import Dict, Any


class RealPhotoStudioEnvironmentEngine:
    """
    Trained Real Photo Studio Background Environments for Google Veo AI and Image Generation.
    """

    STUDIO_ENVIRONMENTS = {
        "CLEAN_CYCLORAMA_INFINITY_STUDIO": {
            "name": "Seamless Off-White Cyclorama Studio",
            "background_description": (
                "Professional seamless off-white to light-grey infinity cyclorama studio wall with smooth floor curve, "
                "polished matte studio floor, zero clutter, high-end high-fashion catalog backdrop with soft falloff."
            ),
            "surface_texture": "Seamless matte cyclorama paper floor with subtle realistic contact shadows beneath footwear.",
            "lighting_setup": "Dual overhead diffused softbox studio lights creating soft, realistic ground shadow fill without harsh lines.",
            "lens_setting": "85mm f/1.8 portrait lens, shallow depth-of-field with crisp foreground model focus."
        },
        "CRIMSON_RED_NEON_GRID_STUDIO": {
            "name": "Deep Crimson Red Y2K Neon Grid Studio",
            "background_description": (
                "Bold deep crimson red square tiled grid wall illuminated by top red overhead light strip, "
                "creating a vibrant Y2K streetwear high-fashion energy."
            ),
            "surface_texture": "Glossy red square ceramic wall tiles with dark grout lines, dark reflective floor surface.",
            "lighting_setup": "High-contrast dramatic red ambient neon lighting with sharp white rim highlights on model shoulders and hair.",
            "lens_setting": "24mm f/2.8 low-angle wide lens for intense editorial streetwear perspective."
        },
        "GOLDEN_HOUR_MINIMALIST_STUDIO": {
            "name": "Sun-Dappled Warm Sand Studio",
            "background_description": (
                "High-end warm sand-beige plaster studio wall with crisp diagonal golden hour sunbeam window pane shadows, "
                "a ceramic vase with dried pampas grass and a potted olive tree branch in the soft background bokeh."
            ),
            "surface_texture": "Textured lime-washed beige wall plaster and smooth micro-cement floor.",
            "lighting_setup": "Warm 4500K golden hour directional window sunlight streaming across background with soft warm fill light.",
            "lens_setting": "50mm f/1.4 prime lens with natural creamy background blur."
        },
        "KOREAN_ARCHWAY_CUBE_STUDIO": {
            "name": "Korean Minimalist Archway Alcove Studio",
            "background_description": (
                "Off-white minimalist studio corner featuring a soft architectural arched alcove, a white geometric studio cube block seat, "
                "and a warm floor lamp ambient glow in the background."
            ),
            "surface_texture": "Clean matte off-white plaster with subtle geometric architectural depth.",
            "lighting_setup": "Soft gradient studio rim lighting with subtle floor reflection and gentle warm accent lamp glow.",
            "lens_setting": "35mm f/2.0 lens capturing environmental context and model silhouette."
        },
        "URBAN_CONCRETE_STREET_STUDIO": {
            "name": "Textured Grey Concrete Outdoor Studio",
            "background_description": (
                "Urban textured grey concrete studio wall with subtle architectural lines, clean asphalt pavement, "
                "and aesthetic street side cafe backdrop."
            ),
            "surface_texture": "Raw grey concrete wall texture with realistic weathering and smooth pavement contact.",
            "lighting_setup": "Bright natural open-shade outdoor daylight with soft ambient sky bounce light.",
            "lens_setting": "24mm f/2.8 low-angle street photography lens."
        },
        "HIGH_KEY_CATALOG_STUDIO": {
            "name": "High-Key Bright Editorial Studio",
            "background_description": (
                "Pure neutral light beige/ivory studio backdrop with soft light falloff, creating a pristine luxury e-commerce fashion aesthetic."
            ),
            "surface_texture": "Smooth studio floor paper roll with soft blurred contact shadows.",
            "lighting_setup": "Large wrap-around octabox lighting setup for ultra-smooth skin tones and zero harsh shadows.",
            "lens_setting": "85mm f/1.8 fashion portrait lens."
        },
        "NIGHT_FLASH_STAIRS_STUDIO": {
            "name": "Night Flash Concrete Stairs Studio",
            "background_description": (
                "Urban concrete outdoor stairs at night with dark urban wall background and subtle ambient city glow."
            ),
            "surface_texture": "Rough textured concrete steps and dark brick backdrop.",
            "lighting_setup": "Direct hard camera flash photography producing sharp direct highlights and deep moody background drop-off.",
            "lens_setting": "35mm f/2.8 direct flash instant film aesthetic."
        }
    }

    @classmethod
    def get_studio_environment(cls, env_key: str | None = None) -> Dict[str, Any]:
        """Returns specific studio env or picks a random high-quality environment."""
        if env_key and env_key in cls.STUDIO_ENVIRONMENTS:
            selected_key = env_key
            env_info = cls.STUDIO_ENVIRONMENTS[env_key]
        else:
            selected_key, env_info = random.choice(list(cls.STUDIO_ENVIRONMENTS.items()))

        return {
            "env_key": selected_key,
            "name": env_info["name"],
            "background_prompt": env_info["background_description"],
            "surface_texture": env_info["surface_texture"],
            "lighting_prompt": env_info["lighting_setup"],
            "lens_setting": env_info["lens_setting"]
        }

    @classmethod
    def format_full_studio_prompt(
        cls,
        outfit_description: str,
        pose_description: str,
        env_key: str | None = None,
        face_consistency_token: str | None = None
    ) -> str:
        """
        Builds complete hyper-realistic photo studio generation prompt with face identity consistency.
        """
        env = cls.get_studio_environment(env_key)
        face_token = f" Face identity: {face_consistency_token}." if face_consistency_token else ""

        return (
            f"Hyper-realistic 8K fashion editorial photo in a professional photo studio. "
            f"Model outfit: {outfit_description}. "
            f"Model pose: {pose_description}.{face_token} "
            f"Studio background: {env['background_prompt']} "
            f"Surface & details: {env['surface_texture']} "
            f"Lighting physics: {env['lighting_prompt']} "
            f"Camera & Optics: {env['lens_setting']}, shot on iPhone 16 Pro / Hasselblad H6D, "
            f"real skin pores and fabric weave texture, zero smooth CGI blur, realistic contact shadows."
        )


if __name__ == "__main__":
    engine = RealPhotoStudioEnvironmentEngine()
    sample_env = engine.get_studio_environment("CLEAN_CYCLORAMA_INFINITY_STUDIO")
    print("\n[Trained Studio Environment]:")
    print("Name:", sample_env["name"])
    print("Background Prompt:", sample_env["background_prompt"])
    print("Surface Texture:", sample_env["surface_texture"])
    print("Lighting:", sample_env["lighting_prompt"])
    print("Lens Setting:", sample_env["lens_setting"])

    print("\n[Full Formatted Studio Prompt]:")
    print(engine.format_full_studio_prompt(
        outfit_description="Oversized navy #86 jersey top with charcoal baggy denim cargos and chunky retro sneakers",
        pose_description="Low-angle sneaker squat crouching low towards camera with chin resting on hand",
        env_key="CLEAN_CYCLORAMA_INFINITY_STUDIO",
        face_consistency_token="Exact trained Asian female model face from reference dataset model_face_1.jpg to model_face_5.jpg"
    ))

