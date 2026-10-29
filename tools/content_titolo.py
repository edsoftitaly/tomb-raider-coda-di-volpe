"""Title level: the Tindari terrain with a looping flyby (sequence 0) over the Laghetti.

Compiled to Engine\\Data\\title.ten (the title level of the Gameflow). Lara is hidden in the title
(Flow.EnableLaraInTitle(false)) but the level still needs her object.
"""
import kit as K

DECOR = dict(centre=(200, 225, 25))


def build(ctx):
    ctx.decor_block = list(getattr(ctx, "decor_block", [])) + [(204, 198, 252, 232)]
    k = ctx.kit
    import content_tindari
    content_tindari.santuario_scene(ctx)
    x, z = k.spot(246, 172)
    k.place(K.LARA, x, z, rot=0.0, name="lara_titolo")
    k.room_at(x, z).no_path = False   # at least one room with boxes, like every other level


def prepare(world):
    import content_tindari
    if hasattr(content_tindari, "prepare"):
        content_tindari.prepare(world)
