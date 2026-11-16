from pathlib import Path
from PIL import Image

repo = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
lock = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\coffee_clips\lyra_lock")
lock.mkdir(exist_ok=True)
ref = Image.open(repo / "lyra_ref.png").convert("RGB")
w, h = ref.size
cell_w, cell_h = w // 2, h // 2
solid = ref.crop((0, 0, cell_w, cell_h))
fw, fh = solid.size
face = solid.crop((int(fw * 0.22), int(fh * 0.08), int(fw * 0.78), int(fh * 0.72)))
solid.save(lock / "lyra_panel_solid.jpg", quality=95)
face.save(lock / "lyra_face_crop.jpg", quality=95)
holo = ref.crop((cell_w, 0, w, cell_h))
holo.save(lock / "lyra_panel_holo_face.jpg", quality=95)
src = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\lyra-refs\lyra_face_source.png")
if src.exists():
    Image.open(src).convert("RGB").save(lock / "lyra_face_source.jpg", quality=95)
print("ok", face.size)
