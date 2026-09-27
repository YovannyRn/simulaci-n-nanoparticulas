"""Motor 2D de adsorción de azul de metileno: movimiento, contacto y adsorción.

No es dinámica molecular. Langmuir y el modelo cinético de referencia
viven en otros módulos y no obligan a este motor a terminar en un qe.
"""

from go_mb.config import SimulationConfig, default_config
from go_mb.engine import run_simulation

__all__ = ["SimulationConfig", "default_config", "run_simulation"]
