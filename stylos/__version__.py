# stylos/__version__.py
# Semantic Versioning
__version__ = "1.2.3"

"""
PATCH: Cambios menores que no rompen la compatibilidad con versiones anteriores. 1.2.3 -> 1.0.1 
MINOR: Cambios que añaden funcionalidad pero mantienen la compatibilidad con versiones anteriores. 1.2.3 -> 1.2.3
MAJOR: Cambios que rompen la compatibilidad con versiones anteriores. 1.2.3 -> 2.0.0

$ bump-my-version patch
$ bump-my-version minor
$ bump-my-version major

$ git push --tags # para que se creen las tags en github
"""