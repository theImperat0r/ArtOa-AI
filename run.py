# ░█████╗░██████╗░████████╗░█████╗░░█████╗░
# ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗
# ███████║██████╔╝░░░██║░░░██║░░██║███████║
# ██╔══██║██╔══██╗░░░██║░░░██║░░██║██╔══██║
# ██║░░██║██║░░██║░░░██║░░░╚█████╔╝██║░░██║
# ╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝


#           ┃┃   (ioseb)
# ╭┳━━┳━━┳━━┫╰━╮
# ┣┫╭╮┃━━┫┃━┫╭╮┃ Kutateladze
# ┃┃╰╯┣━━┃┃━┫╰╯┃ pr0ger.iossb@gmail.com
# ╰┻━━┻━━┻━━┻━━╯ 598508571 (telegram)


# This code is a microservice.
# For StartUp ArtOa
# Let's see how it works step by step.

# Run: uvicorn run:app --reload


from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional
import os
import hashlib
from PIL import Image
import openai
import requests
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import json
from rembg import remove
import cv2
import numpy as np
from fastapi.staticfiles import StaticFiles

app = FastAPI()

openai.api_key = "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"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAVE_PATH = "generated_images"
os.makedirs(SAVE_PATH, exist_ok=True)

app.mount("/generated_images", StaticFiles(directory=SAVE_PATH), name="generated_images")

async def generate_image(prompt: str) -> Optional[Image.Image]:
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt + " | transparent background, separate objects and background. Stylish Minimalistic Graffiti style.", 
            n=1,
            size="1792x1024"
        )
        image_url = response['data'][0]['url']
        image_data = requests.get(image_url)
        image_data.raise_for_status()
        return Image.open(BytesIO(image_data.content))
    except Exception as e:
        print(f"Error IMG generate: {e}")  
        return None

from PIL import Image, ImageFilter

from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO

def remove_background(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  
    
    img_byte_array = BytesIO()
    image.save(img_byte_array, format="PNG")
    img_byte_array = img_byte_array.getvalue()

    img_no_bg = remove(img_byte_array)
    img_no_bg = Image.open(BytesIO(img_no_bg)).convert("RGBA")

    img_no_bg = img_no_bg.filter(ImageFilter.SMOOTH_MORE)

    return img_no_bg




def overlay_image(background: Image.Image, foreground: Image.Image, selection: dict) -> Image.Image:
    bg_np = np.array(background.convert("RGBA"))
    fg_np = np.array(foreground.convert("RGBA"))
    bg_height, bg_width = bg_np.shape[:2]

    if not all(key in selection for key in ["width", "height", "startX", "startY"]):
        raise ValueError("Selection must contain 'width', 'height', 'startX', and 'startY'.")

    region_width = int(selection["width"])
    region_height = int(selection["height"])
    start_x = int(selection["startX"])
    start_y = int(selection["startY"])

    fg_resized = cv2.resize(fg_np, (region_width, region_height), interpolation=cv2.INTER_LANCZOS4)

    center_x = start_x + region_width // 2
    center_y = start_y + region_height // 2

    x1 = max(0, center_x - fg_resized.shape[1] // 2)
    y1 = max(0, center_y - fg_resized.shape[0] // 2)
    x2 = min(bg_width, x1 + fg_resized.shape[1])
    y2 = min(bg_height, y1 + fg_resized.shape[0])

    fg_resized_cropped = fg_resized[max(0, y1 - center_y + fg_resized.shape[0] // 2):y2 - y1,
                                     max(0, x1 - center_x + fg_resized.shape[1] // 2):x2 - x1]

    alpha_fg = fg_resized_cropped[:, :, 3] / 255.0

    for c in range(3):
        bg_np[y1:y2, x1:x2, c] = (
            alpha_fg * fg_resized_cropped[:, :, c]
            + (1 - alpha_fg) * bg_np[y1:y2, x1:x2, c]
        )

    return Image.fromarray(bg_np, "RGBA")


def resize_user_image(image: Image.Image, scale_factor: float) -> Image.Image:
    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    return image.resize((new_width, new_height), Image.LANCZOS)

def generate_filename(image: Image.Image) -> str:
    hash_object = hashlib.md5(image.tobytes())
    return f"{hash_object.hexdigest()}.png"

@app.post("/generate/")
async def generate(
    prompt: str = Form(...), 
    background_image: UploadFile = File(...),
    selection: str = Form(...),
    user_image_scale: float = Form(1)
):
    try:
        selection_data = json.loads(selection)
    except json.JSONDecodeError:
        return {"error": "BAD selection data."}
    if not (0.1 <= user_image_scale <= 1.0):
        return {"error": "BAD user image scale."}
    background = Image.open(background_image.file)
    if user_image_scale < 1.0:
        background = resize_user_image(background, user_image_scale)
    if background.mode != "RGBA":
        background = background.convert("RGBA")
    generated_img = await generate_image(prompt)
    if generated_img is None:
        return {"error": "Error IMG generate."}
    generated_img_no_bg = remove_background(generated_img)
    final_img = overlay_image(background, generated_img_no_bg, selection_data)
    filename = generate_filename(final_img)
    final_img.save(os.path.join(SAVE_PATH, filename), format="PNG")
    return {"image_url": f"/generated_images/{filename}", "hash": filename.split(".")[0]}
