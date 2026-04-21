"""
Sharpening algorithms for the Image Editor.
Supports local sharpening filters and a fallback ESRGAN-style enhancement.
"""

from enum import Enum
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np


class SharpenMethod(Enum):
    """Available sharpening methods."""
    UNSHARP_MASK = "Unsharp Mask"
    HIGH_PASS = "High-pass"
    LAPLACIAN = "Laplacian"
    DECONVOLUTION = "Deconvolution"
    ESRGAN = "ESRGAN"


def sharpen_unsharp_mask(image, intensity=1.5):
    """Apply Unsharp Mask sharpening."""
    radius = max(1, int(1.5 * intensity))
    percent = int(100 * intensity)
    threshold = 1
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))


def sharpen_highpass(image, intensity=1.5):
    """Apply high-pass sharpening."""
    image_rgb = image.convert("RGB")
    radius = max(1, int(intensity * 2))
    amount = max(0.5, intensity)

    try:
        import cv2
        arr = np.array(image_rgb, dtype=np.float32)
        blurred = cv2.GaussianBlur(arr, (0, 0), sigmaX=radius)
        highpass = arr - blurred
        result = np.clip(arr + amount * highpass, 0, 255).astype(np.uint8)
        return Image.fromarray(result)
    except ImportError:
        blurred = image_rgb.filter(ImageFilter.GaussianBlur(radius=radius))
        arr = np.array(image_rgb, dtype=np.float32)
        blurred_arr = np.array(blurred, dtype=np.float32)
        highpass = arr - blurred_arr
        result = np.clip(arr + amount * highpass, 0, 255).astype(np.uint8)
        return Image.fromarray(result)


def sharpen_laplacian(image, intensity=1.5):
    """Apply Laplacian sharpening."""
    image_rgb = image.convert("RGB")
    amount = max(0.5, intensity)

    try:
        import cv2
        arr = np.array(image_rgb, dtype=np.float32)
        lap = cv2.Laplacian(arr, cv2.CV_32F, ksize=3)
        result = np.clip(arr - amount * lap, 0, 255).astype(np.uint8)
        return Image.fromarray(result)
    except ImportError:
        kernel = [0, -1, 0, -1, 5, -1, 0, -1, 0]
        return image_rgb.filter(ImageFilter.Kernel((3, 3), kernel, scale=None, offset=0))


def _gaussian_kernel(size=5, sigma=1.0):
    ax = np.arange(-(size // 2), size // 2 + 1, dtype=np.float32)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    return kernel / np.sum(kernel)


def _richardson_lucy(image_channel, psf, iterations):
    from scipy.signal import fftconvolve
    image_channel = np.clip(image_channel, 0.0, 1.0)
    estimate = np.full_like(image_channel, 0.5)
    psf_mirror = psf[::-1, ::-1]

    for _ in range(iterations):
        conv = fftconvolve(estimate, psf, mode="same")
        relative_blur = image_channel / np.clip(conv, 1e-7, None)
        estimate *= fftconvolve(relative_blur, psf_mirror, mode="same")

    return np.clip(estimate, 0.0, 1.0)


def sharpen_deconvolution(image, intensity=1.5):
    """Apply simple Richardson-Lucy deconvolution sharpening."""
    try:
        from scipy.signal import fftconvolve  # noqa: F401
    except ImportError:
        return sharpen_unsharp_mask(image, intensity=intensity)

    image_rgb = image.convert("RGB")
    arr = np.array(image_rgb, dtype=np.float32) / 255.0
    iterations = max(1, min(20, int(intensity * 5)))
    psf = _gaussian_kernel(size=5, sigma=1.0)

    channels = []
    for c in range(arr.shape[2]):
        channel = arr[:, :, c]
        result = _richardson_lucy(channel, psf, iterations)
        channels.append(result)

    out = np.stack(channels, axis=2)
    return Image.fromarray((np.clip(out, 0.0, 1.0) * 255).astype(np.uint8))


def sharpen_esrgan(image, intensity=1.5):
    """Apply ESRGAN-style enhancement with a local fallback if no model is available."""
    image_rgb = image.convert("RGB")

    # Try a lightweight local enhancement using OpenCV if available.
    try:
        import cv2
        arr = np.array(image_rgb, dtype=np.uint8)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        enhanced = cv2.detailEnhance(bgr, sigma_s=10, sigma_r=0.15)
        enhanced = cv2.edgePreservingFilter(enhanced, flags=1, sigma_s=60, sigma_r=0.4)
        result = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception:
        enhancer = ImageEnhance.Sharpness(image_rgb)
        return enhancer.enhance(1.0 + intensity)


def sharpen_image(image, intensity, method=SharpenMethod.UNSHARP_MASK):
    """Sharpen an image using the selected method."""
    if method == SharpenMethod.UNSHARP_MASK:
        return sharpen_unsharp_mask(image, intensity)
    if method == SharpenMethod.HIGH_PASS:
        return sharpen_highpass(image, intensity)
    if method == SharpenMethod.LAPLACIAN:
        return sharpen_laplacian(image, intensity)
    if method == SharpenMethod.DECONVOLUTION:
        return sharpen_deconvolution(image, intensity)
    if method == SharpenMethod.ESRGAN:
        return sharpen_esrgan(image, intensity)
    return sharpen_unsharp_mask(image, intensity)


def get_method_description(method):
    """Get a description of the sharpening method."""
    descriptions = {
        SharpenMethod.UNSHARP_MASK: "Classic sharpening using Unsharp Mask. Good balance of clarity and artifact control.",
        SharpenMethod.HIGH_PASS: "High-pass sharpening increases local contrast by boosting edge details.",
        SharpenMethod.LAPLACIAN: "Laplacian sharpening emphasizes edges using second-derivative filtering.",
        SharpenMethod.DECONVOLUTION: "Deconvolution sharpening attempts to reverse blur with a PSF-based approach.",
        SharpenMethod.ESRGAN: "ESRGAN-style detail enhancement. Uses local enhancement if no model is available.",
    }
    return descriptions.get(method, "")
