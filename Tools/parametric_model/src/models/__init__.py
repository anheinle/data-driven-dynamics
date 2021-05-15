"""Provides interface to access all modules available in the model directly"""

__author__ = "Manuel Galliker"
__maintainer__ = "Manuel Galliker"
__license__ = "BSD 3"

from . import aerodynamic_models
from . import rotor_models
from . import model_plots
from .dynamics_model import DynamicsModel
from . import quad_plane_model
from .quad_plane_model import QuadPlaneModel
from . import delta_quad_plane_model
from .delta_quad_plane_model import DeltaQuadPlaneModel
from . import quadrotor_model
from .quadrotor_model import QuadRotorModel
from . import model_config
from . model_config import ModelConfig
from . import tilt_wing_model
from . tilt_wing_model import TiltWingModel
