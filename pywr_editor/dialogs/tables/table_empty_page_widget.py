from typing import TYPE_CHECKING

from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from pywr_editor.form import FormTitle
from pywr_editor.style import Color
from pywr_editor.widgets import PushButton

if TYPE_CHECKING:
    from .table_pages_widget import TablePagesWidget


class TableEmptyPageWidget(QWidget):
    def __init__(self, parent: "TablePagesWidget" = None):
        """
        Initialises the empty page widget.
        :param parent: The parent widget.
        """
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = FormTitle("Tables")
        label = QLabel()
        label.setText(
            "Select the table you would like to edit on the list on the left-hand "
            + "side. Otherwise click the 'Add' button to add a new table to the model "
            + "configuration."
        )
        label.setStyleSheet(f"color: {Color('gray', 500).hex}")
        label.setWordWrap(True)

        icon_layout = QHBoxLayout()
        icon_layout.addItem(
            QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        icon = QSvgWidget(":misc/table-dialog")
        icon.setFixedSize(200, 200)
        icon_layout.addWidget(icon)

        # buttons
        close_button = PushButton("Close")
        # noinspection PyUnresolvedReferences
        close_button.clicked.connect(parent.dialog.reject)

        add_button = PushButton("Add new table")
        add_button.setObjectName("add_button")
        # noinspection PyUnresolvedReferences
        add_button.clicked.connect(parent.on_add_new_table)

        button_box = QHBoxLayout()
        button_box.addStretch()
        button_box.addWidget(add_button)
        button_box.addWidget(close_button)

        layout.addWidget(title)
        layout.addLayout(icon_layout)
        layout.addWidget(label)
        layout.addItem(
            QSpacerItem(10, 30, QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        layout.addLayout(button_box)
