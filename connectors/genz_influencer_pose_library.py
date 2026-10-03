"""
GenZ AI Influencer Pose & iPhone Photography Aesthetic Library.
Trains Gemini Vision, Google Veo AI, and Image Generation engines on viral Pinterest/Instagram AI Influencer poses (@derosa_finds aesthetic).

Features 6 Trained Pose Categories:
1. MIRROR_SELFIE_FLASH_POSE: Model holding iPhone in front of aesthetic mirror, cute phone case, showing full-length outfit with subtle flash.
2. HAIR_TUCK_WINDOW_LIGHT: Standing near soft window daylight, one hand casually tucking curtain bangs behind ear, showing neckline & top fit.
3. BEDROOM_CROSS_LEGGED_LAZY: Sitting cross-legged on white linen bed with Kinfolk magazine and coffee mug, casual relaxed influencer vibe.
4. OVER_SHOULDER_CANDID_GLANCE: Over-the-shoulder candid glance towards camera while walking past white paneled door.
5. PRODUCT_DETAIL_TEXTURE_HOLD: Close-up hands holding fabric texture or silver jhumkas towards camera with soft portrait blur.
6. FLATLAY_CREATOR_HANDS_IN_FRAME: Top-down POV angle showing manicured hands arranging 4-piece outfit on white linen bedsheet.

iPhone Camera Aesthetics:
- Shot on iPhone 16 Pro, 24mm / 85mm lens, natural film grain, golden hour daylight, direct flash highlights, raw social media photography look, ZERO CGI smooth skin.
"""
from __future__ import annotations

import random
from typing import Dict, Any, List


class GenZInfluencerPoseLibrary:
    """
    Trained GenZ AI Influencer Pose & iPhone Visual Library.
    """

    IPHONE_CAMERA_TOKENS = (
        "Shot on iPhone 16 Pro, 24mm lens, crisp natural skin texture, golden hour daylight, "
        "raw unedited Instagram aesthetic, realistic film grain, zero CGI smooth skin, 8K ultra-detailed."
    )

    POSES = {
        "MIRROR_SELFIE_FLASH_POSE": {
            "name": "GenZ Mirror Selfie with iPhone",
            "pose_description": (
                "Model standing in front of an aesthetic full-length bedroom mirror, holding a chic iPhone with a cute phone case, "
                "tilting her head slightly with a serene half-smile, displaying her complete outfit fit in the mirror reflection."
            ),
            "camera_angle": "Eye-level mirror reflection shot",
            "lighting": "Soft indoor ambient daylight with subtle mirror flash reflection"
        },
        "HAIR_TUCK_WINDOW_LIGHT": {
            "name": "Candid Hair-Tuck Window Daylight Pose",
            "pose_description": (
                "Model standing casually near a sunlit window, one hand naturally tucking her soft dark curtain bangs behind her ear, "
                "gaze soft and romantic towards the camera, highlighting her silver oxidised jhumkas and neckline fit."
            ),
            "camera_angle": "Medium 85mm portrait shot",
            "lighting": "Warm golden hour natural window sunlight streaming across face"
        },
        "BEDROOM_CROSS_LEGGED_LAZY": {
            "name": "Lazy Sunday Bedroom Sitting Pose",
            "pose_description": (
                "Model sitting cross-legged casually on a white linen bed, leaning on one hand with a coffee mug and Kinfolk magazine nearby, "
                "relaxed candid posture showcasing the comfortable drape of her top and wide-leg jeans."
            ),
            "camera_angle": "Slightly elevated 45-degree angle",
            "lighting": "Warm morning sunlight filtering through sheer curtains"
        },
        "OVER_SHOULDER_CANDID_GLANCE": {
            "name": "Over-the-Shoulder Candid Glance",
            "pose_description": (
                "Model walking past a white paneled shutter door, turning her head back over her shoulder with a relaxed elegant smile, "
                "showing the silhouette, back pattern, and waist tailoring of her outfit."
            ),
            "camera_angle": "Candid street-style over-the-shoulder tracking shot",
            "lighting": "Bright natural outdoor daylight"
        },
        "PRODUCT_DETAIL_TEXTURE_HOLD": {
            "name": "Fabric Texture & Detail Close-Up",
            "pose_description": (
                "Close-up shot of model's manicured hands holding up the fabric hem and dori tassels of her outfit towards the iPhone camera, "
                "with her face softly blurred in the background portrait bokeh."
            ),
            "camera_angle": "Macro close-up portrait shot",
            "lighting": "Direct soft daylight highlighting fabric weave and embroidery"
        },
        "FLATLAY_CREATOR_HANDS_IN_FRAME": {
            "name": "Pinterest 4-Piece Flatlay Combo POV",
            "pose_description": (
                "Top-down 90-degree POV shot showing model's hands placing the final Y2K handbag next to a styled outfit combo "
                "(graphic baby tee + denim jeans + retro brown sneakers) laid out on a white linen bedsheet."
            ),
            "camera_angle": "Vertical top-down flatlay angle",
            "lighting": "Flat even studio daylight"
        }
    }

    @classmethod
    def get_pose(cls, pose_key: str | None = None) -> Dict[str, Any]:
        """Returns specific pose dict or picks a random GenZ pose."""
        if pose_key and pose_key in cls.POSES:
            pose_info = cls.POSES[pose_key]
        else:
            pose_key, pose_info = random.choice(list(cls.POSES.items()))

        return {
            "pose_key": pose_key,
            "pose_name": pose_info["name"],
            "description": pose_info["pose_description"],
            "camera_angle": pose_info["camera_angle"],
            "lighting": pose_info["lighting"],
            "camera_tokens": cls.IPHONE_CAMERA_TOKENS
        }

    @classmethod
    def format_influencer_prompt(cls, outfit_name: str, pose_key: str | None = None) -> str:
        """Constructs full AI Influencer prompt with GenZ pose and iPhone camera aesthetic."""
        p = cls.get_pose(pose_key)
        return (
            f"Hyper-realistic 4K 60fps GenZ AI Influencer photoshoot. "
            f"Outfit: {outfit_name}. "
            f"Pose: {p['description']} "
            f"Camera & Angle: {p['camera_angle']}. "
            f"Lighting: {p['lighting']}. "
            f"{p['camera_tokens']}"
        )


if __name__ == "__main__":
    lib = GenZInfluencerPoseLibrary()
    print("\n[Sample Trained GenZ Influencer Pose Prompt]:")
    print(lib.format_influencer_prompt("a lavender flame knit sweater and black wide-leg denim jeans", "MIRROR_SELFIE_FLASH_POSE"))
