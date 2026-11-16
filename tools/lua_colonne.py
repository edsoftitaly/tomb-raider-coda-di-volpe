"""16 Nov (Ed): no custom music in the level scripts, only the TR2 and TR3 soundtracks. Every cue of CDV.MUSIC
(and the one track played directly) gets a track of those two games; the files are copied to Engine\\Audio under
the names of TRACKS.

  lua_colonne.py <dir> Oliveri_k.lua:Oliveri_l.lua Marinello_h.lua:Marinello_i.lua ...   patch the scripts
  lua_colonne.py --list                                                                  source file -> audio name"""
import os
import re
import sys

T2 = "04 TOMB RAIDER II# STARRING LARA CROFT (RERENDERED SOUNDTRACK)"
T3 = "06 TOMB RAIDER III# ADVENTURES OF LARA CROFT (RERENDERED SOUNDTRACK)"
# audio name -> (folder, source file without ".mp3")
TRACKS = {
    "tr2_03_end_titles": (T2, "03. Snowmobile Theme - End Titles (Rerendered)"),
    "tr2_04_snowmobile_escape": (T2, "04. Snowmobile Escape! (Rerendered)"),
    "tr2_05_vertigo": (T2, "05. Vertigo (Rerendered)"),
    "tr2_06_choral": (T2, "06. Choral Tomb Raider (Rerendered)"),
    "tr2_07_incidental_1": (T2, "07. Incidental 1 (Rerendered)"),
    "tr2_08_incidental_2": (T2, "08. Incidental 2 (Rerendered)"),
    "tr2_09_incidental_3": (T2, "09. Incidental 3 (Rerendered)"),
    "tr2_10_incidental_4": (T2, "10. Incidental 4 (Rerendered)"),
    "tr2_11_incidental_5": (T2, "11. Incidental 5 (Rerendered)"),
    "tr2_12_incidental_6": (T2, "12. Incidental 6 (Rerendered)"),
    "tr2_13_incidental_7": (T2, "13. Incidental 7 (Rerendered)"),
    "tr2_14_incidental_8": (T2, "14. Incidental 8 (Rerendered)"),
    "tr2_16_tension_1": (T2, "16. Tension 1 (Rerendered)"),
    "tr2_17_tension_2": (T2, "17. Tension 2 (Rerendered)"),
    "tr2_18_tension_3": (T2, "18. Tension 3 (Rerendered)"),
    "tr2_19_tension_4": (T2, "19. Tension 4 (Rerendered)"),
    "tr2_20_short_choral": (T2, "20. Short Choral (Rerendered)"),
    "tr2_22_short_2": (T2, "22. Short 2 (Rerendered)"),
    "tr2_25_secret": (T2, "25. Secret (Rerendered)"),
    "tr3_04_shes_cool": (T3, "04. She's Cool (Rerendered)"),
    "tr3_07_tony_the_loon": (T3, "07. Tony The Loon (Rerendered)"),
    "tr3_08_long_way_up": (T3, "08. Long Way Up (Rerendered)"),
    "tr3_09_kneel_and_pray": (T3, "09. Kneel and Pray (Rerendered)"),
    "tr3_14_butterflies_2": (T3, "14. There Be Butterflies Here 2 (Rerendered)"),
    "tr3_15_butterflies_3": (T3, "15. There Be Butterflies Here 3 (Rerendered)"),
    "tr3_19_mind_the_gap_2": (T3, "19. Mind The Gap 2 (Rerendered)"),
    "tr3_20_around_the_corner_1": (T3, "20. Around the Corner 1 (Rerendered)"),
    "tr3_21_around_the_corner_2": (T3, "21. Around the Corner 2 (Rerendered)"),
    "tr3_22_around_the_corner_3": (T3, "22. Around the Corner 3 (Rerendered)"),
    "tr3_26_seeing_is_believing_1": (T3, "26. Seeing Is Believing 1 (Rerendered)"),
    "tr3_27_seeing_is_believing_2": (T3, "27. Seeing Is Believing 2 (Rerendered)"),
    "tr3_28_look_what_we_have_here_1": (T3, "28. Look What We Have Here 1 (Rerendered)"),
    "tr3_29_look_what_we_have_here_2": (T3, "29. Looky What We Have Here 2 (Rerendered)"),
    "tr3_30_look_what_we_have_here_3": (T3, "30. Looky What We Have Here 3 (Rerendered)"),
    "tr3_40_stone_the_crows_10": (T3, "40. Stone The Crows 10 (Rerendered)"),
    "tr3_41_look_out_1": (T3, "41. Look Out 1 (Rerendered)"),
    "tr3_42_look_out_2": (T3, "42. Look Out 2 (Rerendered)"),
    "tr3_43_look_out_3": (T3, "43. Look Out 3 (Rerendered)"),
    "tr3_44_look_out_4": (T3, "44. Look Out 4 (Rerendered)"),
    "tr3_45_look_out_5": (T3, "45. Look Out 5 (Rerendered)"),
    "tr3_48_look_out_8": (T3, "48. Look Out 8 (Rerendered)"),
    "tr3_49_greedy_mob": (T3, "49. Greedy Mob (Rerendered)"),
}
CUES = {
    "Oliveri": {
        "inizio": "tr2_07_incidental_1", "primo": "tr2_17_tension_2", "drop_chiave": "tr3_28_look_what_we_have_here_1",
        "tetto": "tr2_10_incidental_4", "use_argano": "tr2_22_short_2", "cortile": "tr3_49_greedy_mob",
        "fine": "tr3_04_shes_cool", "segreto": "tr2_25_secret"},
    "Marinello": {
        "inizio": "tr2_08_incidental_2", "piazzale": "tr2_16_tension_1", "agguato_reti": "tr3_41_look_out_1",
        "use_chiusa": "tr3_26_seeing_is_believing_1", "fondo": "tr2_11_incidental_5", "canneto": "tr3_14_butterflies_2",
        "casello": "tr3_45_look_out_5", "chiave_casello": "tr3_28_look_what_we_have_here_1",
        "use_chiusa2": "tr2_12_incidental_6", "g1": "tr3_40_stone_the_crows_10",
        "canto_ok": "tr3_27_seeing_is_believing_2", "laghetto": "tr3_15_butterflies_3", "masso_g": "tr3_43_look_out_3",
        "scala": "tr3_08_long_way_up", "segreto": "tr2_25_secret"},
    "Tindari": {
        "inizio": "tr3_22_around_the_corner_3", "campo": "tr2_18_tension_3", "teatro": "tr3_44_look_out_4",
        "casa": "tr3_20_around_the_corner_1", "peristilio": "tr3_21_around_the_corner_2",
        "mosaico": "tr3_19_mind_the_gap_2", "basilica": "tr2_19_tension_4", "terrazza": "tr3_48_look_out_8",
        "belvedere": "tr2_05_vertigo", "santuario": "tr3_09_kneel_and_pray", "cripta": "tr2_20_short_choral",
        "astro": "tr3_29_look_what_we_have_here_2", "gemelli": "tr3_30_look_what_we_have_here_3",
        "pozzo": "tr2_14_incidental_8", "segreto": "tr2_25_secret"},
    "Sommersa": {
        "inizio": "tr2_13_incidental_7", "decumano": "tr2_06_choral", "terme_acqua": "tr2_22_short_2",
        "cisterna": "tr3_27_seeing_is_believing_2", "cancello": "tr3_28_look_what_we_have_here_1",
        "tempio": "tr2_09_incidental_3", "turi": "tr3_07_tony_the_loon", "drop_polluce": "tr3_29_look_what_we_have_here_2",
        "use_altare2": "tr2_04_snowmobile_escape", "masso_fuga": "tr3_43_look_out_3", "fine": "tr2_03_end_titles",
        "segreto": "tr2_25_secret"},
}
DIRECT = {"cdv_donna_villa_grido": "tr3_42_look_out_2"}     # CDV.Track("...") outside the table


def patch(text, level):
    cues = dict(CUES[level])
    a = text.index("CDV.MUSIC = {")
    b = text.index("}", a)
    block = text[a:b]
    seen = set()

    def sub(m):
        key = m.group(2)
        assert key in cues, (level, key)
        seen.add(key)
        return '%s%s = "%s",' % (m.group(1), key, cues[key])
    block = re.sub(r'^(\s*)(\w+) = "[\w]+",', sub, block, flags=re.M)
    assert seen == set(cues), (level, set(cues) ^ seen)
    text = text[:a] + block + text[b:]
    for old, new in DIRECT.items():
        text = text.replace('CDV.Track("%s")' % old, 'CDV.Track("%s")' % new)
    left = [n for n in re.findall(r'CDV\.Track\("(\w+)"\)', text) if n not in TRACKS]
    assert not left, left
    return text


if __name__ == "__main__":
    if sys.argv[1] == "--list":
        for name, (folder, f) in sorted(TRACKS.items()):
            print("%s\t%s/%s.mp3" % (name, folder, f))
    else:
        d = sys.argv[1]
        for pair in sys.argv[2:]:
            src, dst = pair.split(":")
            level = src.split("_")[0]
            t = open(os.path.join(d, src), encoding="utf-8", newline="").read()
            open(os.path.join(d, dst), "w", encoding="utf-8", newline="").write(patch(t, level))
            print(level, "->", dst)
    used = set(v for c in CUES.values() for v in c.values()) | set(DIRECT.values())
    assert used == set(TRACKS), used ^ set(TRACKS)
