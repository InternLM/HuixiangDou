from web.model.base import Image


def detect_base64_image_suffix(base64: str) -> [Image, str]:
    if not base64 or len(base64) == 0:
        return [Image.INVALID, '']

    s = base64.split('base64,')
    if len(s) < 2:
        return [Image.INVALID, '']

    base64_prefix = s[0].lower()
    if 'data:image/jpeg;' == base64_prefix:
        return [Image.JPG, s[1]]
    if 'data:image/png;' == base64_prefix:
        return [Image.PNG, s[1]]
    if 'data:image/bmp;' == base64_prefix:
        return [Image.BMP, s[1]]

    return [Image.INVALID, '']
