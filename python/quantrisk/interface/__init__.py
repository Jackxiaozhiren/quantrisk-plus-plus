"""The interface surfaces: what this repository shows a reader who will not install it.

The lane's ordering is a chain before a surface, and this package holds only what comes after the
chain: a generator that reads the evidence instead of describing it. Nothing here may contain a
figure that did not come out of a committed artifact during the build, and nothing here publishes
anything — the generated pages are written into an ignored directory, and deploying them is a
separate unit with its own approval.
"""
