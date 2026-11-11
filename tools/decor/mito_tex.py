"""Textures of the mythic props (cave of Donna Villa, Tindari, the temple): photographic CC0 plus flat metals."""
from decor.marinello_tex import photo
from decor.tex import solid


def build(pk):
    pk.put("m_marble", photo("concrete005", (256, 256), tint=(1.0, 0.95, 0.84), gain=1.05))
    pk.put("m_limestone", photo("rock003", (256, 256), tint=(1.0, 0.93, 0.78), gain=0.95))
    pk.put("m_cave", photo("rock022", (256, 256), tint=(0.84, 0.82, 0.8), gain=0.62))
    pk.put("m_bronze", solid(64, 64, (96, 128, 104), 71, 0.3, 8))
    pk.put("m_gold", solid(64, 64, (214, 170, 62), 72, 0.25, 8))
    pk.put("m_shell", solid(64, 64, (226, 200, 176), 73, 0.2, 6))
    pk.put("m_orange", solid(64, 64, (226, 110, 30), 74, 0.12, 4))
    pk.put("m_yellow", solid(32, 32, (220, 190, 40), 75, 0.1, 4))
