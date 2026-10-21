"""The verification instruments: the falsification plants and the harness that fires them.

These are load-bearing claims rather than mere code — `docs/interview_defense.md` quotes what the
sweep rejects — so they live in the installable package, importable and type-checked like the rest
of the surface. The plant list is a separate module from the interpreter on purpose: finding 94
records that a plant anchoring on a line of the file that holds the list finds that line twice, and
the case is then refused before it runs.
"""
