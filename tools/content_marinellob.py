"""Livello 1, parte 1, variante di riserva senza flipmap: il Mergolo e' gia' asciutto. Solo se la versione
normale non si carica o il lago non si svuota."""
import content_marinello as C

FRAME = C.FRAME
DECOR = {}


def prepare(world):
    C.NOFLIP = True
    C.prepare(world)


def build(ctx):
    C.NOFLIP = True
    C.build(ctx)
    C.NOFLIP = False
