import os
import logging
from pathlib import Path
from datetime import datetime

import imageio.v2 as imageio
import numpy as np
import cv2
from matplotlib import pyplot as plt
import imgdd as dd


def create_kernals() -> dict[str, np.array]:
    """
    create 5 different filters
    """
    kernals = {}

    kernel_ident = np.zeros((3, 3), np.float32)
    kernel_ident[1, 1] = 1
    kernals["ident"] = kernel_ident

    kernel_sharpen_light = -0.1 * np.ones((3, 3), np.float32)
    kernel_sharpen_light[1, 1] = 2
    kernals["sharpen"] = kernel_sharpen_light

    kernal_emboss = np.array([
        [-2, -1, 0],
        [-1,  1, 1],
        [ 0,  1, 2]
    ])
    kernals["emboss"] = kernal_emboss

    kernel_gaussian = (1/16) * np.array([
        [1, 2, 1],
        [2, 4, 2],
        [1, 2, 1]
    ])
    kernals["gaussian"] = kernel_gaussian

    kernel_motion_blur = (1/3) * np.array([
        [0.5, 0, 0  ],
        [0,   1, 0  ],
        [0,   0, 0.5]
    ])
    kernals["motion_blur"] = kernel_motion_blur

    kernel_light = np.zeros((3, 3), np.float32)
    kernel_light[1, 1] = 1.3
    kernals["light"] = kernel_light

    kernel_dark = np.zeros((3, 3), np.float32)
    kernel_dark[1, 1] = 0.8
    kernals["dark"] = kernel_dark

    return kernals

def apply_kernals(img: np.ndarray, kernals: dict[str, np.array]):
    return [cv2.filter2D(img, -1, kernal) for kernal in kernals.values()]

def apply_scale(img: np.ndarray, scale: float = None) -> np.ndarray:
    """
    apply scaling from 1x to 1.3x
    """
    max_scale = 1.3
    if scale is None:
        scale = np.random.uniform(1.0, max_scale)
    if scale <= 1.0:
        return img.copy()

    h, w = img.shape[:2]
    new_w = int(w * scale)
    new_h = int(h * scale)
    scaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    start_x = (new_w - w) // 2
    start_y = (new_h - h) // 2
    cropped = scaled[start_y:start_y + h, start_x:start_x + w]
    return cropped

def apply_rotate(img: np.ndarray, angle: float = None):
    """
    apply rotation, from -30 to +30
    """
    var_angle = 30
    if angle is None:
        angle = np.random.uniform(-var_angle, var_angle)
    
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img, rotation_matrix, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0)
    )
    return rotated, angle


def apply_bias(img: np.ndarray, bias_range: tuple = (0.7, 0.9)) -> np.ndarray:
    """
    Случайно обрезает изображение до прямоугольника, размер которого составляет
    случайную долю от исходного в пределах bias_range.
    """
    h, w = img.shape[:2]
    crop_coeff = np.random.uniform(bias_range[0], bias_range[1])
    new_h = int(h * crop_coeff)
    new_w = int(w * crop_coeff)
    
    top = np.random.randint(0, h - new_h + 1)
    left = np.random.randint(0, w - new_w + 1)
    
    return img[top:top+new_h, left:left+new_w]

def apply_img_generation(img: np.ndarray, kernals) -> np.ndarray:
    """
    apply rotation, scaling and bias to photo
    """
    postkernals_imgs = apply_kernals(img, kernals)
    imgs = []
    for img in postkernals_imgs:
        rotated, angle = apply_rotate(img)
        rotated_scaled = rotated
        if angle <= 10:
            rotated_scaled = apply_scale(rotated, 1.2) 
        elif angle <= 20:
            rotated_scaled = apply_scale(rotated, 1.3) 
        else:
            rotated_scaled = apply_scale(rotated, 1.5) 
        biased = apply_bias(rotated_scaled)
        imgs.append(biased)
    return imgs

def path_to_image(url):
    image = imageio.imread(url)
    return image

raw_photo_folder = Path("./data/car_clear_parsed")
prepared_data_folder = Path("./data/car_clear_generated")
iter_n = 3

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
_log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

def main():

    duplicates = dd.dupes(path="./data/car_clear_parsed")
    if duplicates:
        log.warning(f"Найдено {len(duplicates)} групп дубликатов. Прерывание.")
        assert len(duplicates) == 0, f"Дубликаты: {duplicates}"
    else:
        log.info("Дубликатов не найдено")

    for i, filename in enumerate(os.listdir(raw_photo_folder)):
        if i % 5 == 0:
            log.info(f"Прогресс: {i}/{len(os.listdir(raw_photo_folder))} файлов")

        if filename[-4:] != ".jpg": continue
        try:
            img = path_to_image(raw_photo_folder / filename)
            kernals = create_kernals()

            for iteration_n in range(1, iter_n+1):
                new_imgs = apply_img_generation(img, kernals)
                base_name = filename.split(".")[0]

                for idx, new_img in enumerate(new_imgs):
                    out_name = f"{base_name}_gen_{(iteration_n-1) * iter_n + idx}.jpg"
                    out_path = prepared_data_folder / out_name
                    imageio.imwrite(out_path, new_img)

        except Exception as e:
            log.error(f"Ошибка при обработке {filename}: {e}", exc_info=True)
    log.info("saved total %s new photos out of %s", len(os.listdir(prepared_data_folder)), len(os.listdir(raw_photo_folder)))


if __name__ == "__main__":
    main()
