"""Convenience re-exports for trace extraction utilities.

Several modules (rhythm, lvh_checklist, precordial_transition, axis_hexaxial)
import ``extract_trace_centerline`` and ``smooth_signal`` from ``cv.trace``.
The canonical implementations live in ``cv.rpeaks_from_image``; this module
simply re-exports them so that both import paths work.
"""

from .rpeaks_from_image import extract_trace_centerline, smooth_signal

__all__ = ["extract_trace_centerline", "smooth_signal"]
