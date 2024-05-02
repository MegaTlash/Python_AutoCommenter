import numpy as np
from scipy import interpolate
from scipy.stats import spearmanr
import warnings
import math
from .base import BaseEstimator, TransformerMixin, RegressorMixin
from .utils import check_array, check_consistent_length
from .utils.validation import _check_sample_weight
from ._isotonic import _inplace_contiguous_isotonic_regression, _make_unique
__all__ = ["check_increasing", "isotonic_regression", "IsotonicRegression"]
def check_increasing(x, y):
    rho, _ = spearmanr(x, y)
    increasing_bool = rho >= 0
    if rho not in [-1.0, 1.0] and len(x) > 3:
        F = 0.5 * math.log((1.0 + rho) / (1.0 - rho))
        F_se = 1 / math.sqrt(len(x) - 3)
        rho_0 = math.tanh(F - 1.96 * F_se)
        rho_1 = math.tanh(F + 1.96 * F_se)
        if np.sign(rho_0) != np.sign(rho_1):
            warnings.warn(
                "Confidence interval of the Spearman "
                "correlation coefficient spans zero. "
                "Determination of ``increasing`` may be "
                "suspect."
            )
    return increasing_bool
def isotonic_regression(
    y, *, sample_weight=None, y_min=None, y_max=None, increasing=True
):
    order = np.s_[:] if increasing else np.s_[::-1]
    y = check_array(y, ensure_2d=False, dtype=[np.float64, np.float32])
    y = np.array(y[order], dtype=y.dtype)
    sample_weight = _check_sample_weight(sample_weight, y, dtype=y.dtype, copy=True)
    sample_weight = np.ascontiguousarray(sample_weight[order])
    _inplace_contiguous_isotonic_regression(y, sample_weight)
    if y_min is not None or y_max is not None:
        if y_min is None:
            y_min = -np.inf
        if y_max is None:
            y_max = np.inf
        np.clip(y, y_min, y_max, y)
    return y[order]
class IsotonicRegression(RegressorMixin, TransformerMixin, BaseEstimator):
    def __init__(self, *, y_min=None, y_max=None, increasing=True, out_of_bounds="nan"):
        self.y_min = y_min
        self.y_max = y_max
        self.increasing = increasing
        self.out_of_bounds = out_of_bounds
    def _check_input_data_shape(self, X):
        if not (X.ndim == 1 or (X.ndim == 2 and X.shape[1] == 1)):
            msg = (
                "Isotonic regression input X should be a 1d array or "
                "2d array with 1 feature"
            )
            raise ValueError(msg)
    def _build_f(self, X, y):
        if self.out_of_bounds not in ["raise", "nan", "clip"]:
            raise ValueError(
                "The argument ``out_of_bounds`` must be in "
                "'nan', 'clip', 'raise'; got {0}".format(self.out_of_bounds)
            )
        bounds_error = self.out_of_bounds == "raise"
        if len(y) == 1:
            self.f_ = lambda x: y.repeat(x.shape)
        else:
            self.f_ = interpolate.interp1d(
                X, y, kind="linear", bounds_error=bounds_error
            )
    def _build_y(self, X, y, sample_weight, trim_duplicates=True):
        self._check_input_data_shape(X)
        X = X.reshape(-1)  
        if self.increasing == "auto":
            self.increasing_ = check_increasing(X, y)
        else:
            self.increasing_ = self.increasing
        sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)
        mask = sample_weight > 0
        X, y, sample_weight = X[mask], y[mask], sample_weight[mask]
        order = np.lexsort((y, X))
        X, y, sample_weight = [array[order] for array in [X, y, sample_weight]]
        unique_X, unique_y, unique_sample_weight = _make_unique(X, y, sample_weight)
        X = unique_X
        y = isotonic_regression(
            unique_y,
            sample_weight=unique_sample_weight,
            y_min=self.y_min,
            y_max=self.y_max,
            increasing=self.increasing_,
        )
        self.X_min_, self.X_max_ = np.min(X), np.max(X)
        if trim_duplicates:
            keep_data = np.ones((len(y),), dtype=bool)
            keep_data[1:-1] = np.logical_or(
                np.not_equal(y[1:-1], y[:-2]), np.not_equal(y[1:-1], y[2:])
            )
            return X[keep_data], y[keep_data]
        else:
            return X, y
    def fit(self, X, y, sample_weight=None):
        check_params = dict(accept_sparse=False, ensure_2d=False)
        X = check_array(X, dtype=[np.float64, np.float32], **check_params)
        y = check_array(y, dtype=X.dtype, **check_params)
        check_consistent_length(X, y, sample_weight)
        X, y = self._build_y(X, y, sample_weight)
        self.X_thresholds_, self.y_thresholds_ = X, y
        self._build_f(X, y)
        return self
    def transform(self, T):
        if hasattr(self, "X_thresholds_"):
            dtype = self.X_thresholds_.dtype
        else:
            dtype = np.float64
        T = check_array(T, dtype=dtype, ensure_2d=False)
        self._check_input_data_shape(T)
        T = T.reshape(-1)  
        if self.out_of_bounds not in ["raise", "nan", "clip"]:
            raise ValueError(
                "The argument ``out_of_bounds`` must be in "
                "'nan', 'clip', 'raise'; got {0}".format(self.out_of_bounds)
            )
        if self.out_of_bounds == "clip":
            T = np.clip(T, self.X_min_, self.X_max_)
        res = self.f_(T)
        res = res.astype(T.dtype)
        return res
    def predict(self, T):
        return self.transform(T)
    def __getstate__(self):
        state = super().__getstate__()
        state.pop("f_", None)
        return state
    def __setstate__(self, state):
        super().__setstate__(state)
        if hasattr(self, "X_thresholds_") and hasattr(self, "y_thresholds_"):
            self._build_f(self.X_thresholds_, self.y_thresholds_)
    def _more_tags(self):
        return {"X_types": ["1darray"]}
