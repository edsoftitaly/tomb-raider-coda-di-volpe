"""Sommersa.lua for Ed's disk: the runtime (prelude and tail) of the installed Tindari.lua, which is the newest one
(hands, wheel sounds, ShowModel, log), with the level data generated here and the music table of Sommersa.

usage: sommersa_installa.py <generated Sommersa.lua> <installed Tindari.lua> <out>"""
import re
import sys

MUSIC = '''CDV.MUSIC = {
    inizio = "cdv_som_inizio",              -- inizio del livello
    decumano = "cdv_som_propileo",          -- la strada romana sott'acqua, il tempio in fondo
    terme_acqua = "cdv_meccanismo",         -- la ruota delle terme: l'acqua sale
    cisterna = "cdv_enigma",                -- la cisterna dei berretti
    cancello = "cdv_chiave",                -- i due pilei: il cancello del tempio si apre
    tempio = "cdv_som_tempio",              -- il tempio
    turi = "cdv_agguato",                   -- Turi 'a Vulpi
    drop_polluce = "cdv_som_polluce",       -- l'Astro di Polluce torna a galla
    use_altare2 = "cdv_som_crollo",         -- i gemelli insieme: il tempio crolla
    masso_fuga = "cdv_masso",               -- il masso
    fine = "cdv_som_fine",                  -- finale
    segreto = "cdv_segreto",                -- ogni Stella dei Dioscuri
}'''
A, B = "-- ----------------------------------------------------------------- level data", "-- Playtest hook"


def cut(s):
    i, j = s.index(A), s.index(B)
    return s[:i], s[i:j], s[j:]


gen = open(sys.argv[1], encoding="utf-8").read().replace("\r\n", "\n")
inst = open(sys.argv[2], encoding="utf-8").read().replace("\r\n", "\n")
head, _, tail = cut(inst)
_, data, _ = cut(gen)
head = head.replace("-- Coda di Volpe - Tindari (", "-- Coda di Volpe - La metà perduta (").replace("Levels\\Tindari.lua", "Levels\\Sommersa.lua")
head, n = re.subn(r"CDV\.MUSIC = \{.*?\n\}", lambda m: MUSIC, head, count=1, flags=re.S)
assert n == 1 and "Tindari" not in head and "Tindari" not in tail.replace("Oliveri = {", ""), "leftovers of Tindari in the runtime"
open(sys.argv[3], "w", encoding="utf-8", newline="\r\n").write(head + data + tail)
