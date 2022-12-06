from PySide6.QtCore import QPoint, QPointF, QSettings

from model import ModelFileInfo
from pywr_editor import MainWindow

class Settings:
    json_file: str | None
    org_name: str
    app_name: str | None
    store_geometry_widget: list[str]

    lock_key: str
    hide_labels_key: str
    hide_arrows_key: str
    zoom_level_key: str
    schematic_center_key: str
    recent_projects_key: str

    def __init__(self, json_file: str | None): ...
    @property
    def instance(self) -> QSettings: ...
    @property
    def global_instance(self) -> QSettings: ...
    def save_window_attributes(self, window: "MainWindow") -> None: ...
    def restore_window_attributes(self, window: "MainWindow") -> None: ...
    @property
    def is_schematic_locked(self) -> bool: ...
    def save_schematic_lock(self, lock: bool) -> None: ...
    @property
    def are_labels_hidden(self) -> bool: ...
    def save_hide_labels(self, hide: bool) -> None: ...
    @property
    def are_edge_arrows_hidden(self) -> bool: ...
    def save_hide_arrows(self, hide: bool) -> None: ...
    @property
    def zoom_level(self) -> float: ...
    def save_zoom_level(self, zoom_level: float) -> None: ...
    @property
    def schematic_center(self) -> QPoint: ...
    def save_schematic_center(
        self, position: [QPointF] | list[QPointF]
    ) -> None: ...
    def get_recent_files(self) -> list[dict[str, str | ModelFileInfo]]: ...
    def save_recent_file(self, file: str) -> None: ...
    def clear_recent_files(self) -> None: ...
    @staticmethod
    def str_to_bool(value: str) -> bool: ...
