from typing import TYPE_CHECKING, Any

import qtawesome as qta
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from pywr_editor.form import FormCustomWidget, FormField, SlotsTableModel, Validation
from pywr_editor.model import NodeConfig
from pywr_editor.style import Color
from pywr_editor.utils import Logging, get_signal_sender, move_row
from pywr_editor.widgets import PushIconButton, TableView

if TYPE_CHECKING:
    from pywr_editor.dialogs import NodeDialogForm

"""
 This widget handles the slot names and extra slots
 for a Multi Split Link node. The slot names are fetched
 from the edges of the nodes, the node is connected to.
 A warning is shown if:
  - the node is not connected at least to 2 nodes (one
    slot generated by the Piece Wise Link and one mandatory
    slot (self.total_extra_slots=1 by default) created by the Multi
    Split Link
  - the node is connected, but the name of the slot in the
    edge does not match the name in slot_names
  - the slot names are not set on the edge

 The widget ignores the value in the extra_slots slot of the
 node dictionary and sets the value based on the number of
 connected nodes minus one. The names in slot_names is ignored
 and the names are fetched from the edges where the Multi Split
 Link node in the source node.
 Finally, Factors as parameters are not supported. and the widget
 does not validate or send any data if the node is not properly
 connected.
"""


class SlotsTableWidget(FormCustomWidget):
    def __init__(
        self,
        name: str,
        value: NodeConfig,
        parent: FormField,
    ):
        """
        Initialises the widget.
        :param name: The field name.
        :param value: The NodeConfig instance of the node.
        :param parent: The parent widget.
        """
        self.logger = Logging().logger(self.__class__.__name__)
        self.logger.debug(f"Loading widget with value {value}")

        # form: NodeDialogForm
        super().__init__(name, value, parent)
        node_dict = value.props
        self.form: "NodeDialogForm"
        model_config = self.form.model_config

        # Get connected nodes from edges
        self.target_nodes = model_config.edges.targets(value.name)
        if self.target_nodes is None:
            self.target_nodes = []
        self.total_edges = len(self.target_nodes)
        self.logger.debug(f"Found {self.total_edges} target nodes: {self.target_nodes}")

        self.edge_slot_names = [
            model_config.edges.slot(value.name, node, 1) for node in self.target_nodes
        ]
        self.logger.debug(f"Found the following edge slots: {self.edge_slot_names}")

        # get provided slot names or use default list
        self.node_config_slot_names = node_dict.get(
            "slot_names", list(range(self.total_edges))
        )

        # calculate number of extra slots the node is connected to
        self.total_extra_slots = self.total_edges - 1
        if self.total_extra_slots <= 0:
            self.total_extra_slots = 0
            # disregard provided names
            self.node_config_slot_names = []

        # get factors - this can be a parameter. For simplicity support
        # only numbers
        self.factors = node_dict.get("factors", [])
        self.factors = [
            factor if isinstance(factor, (int, float)) else None
            for factor in self.factors
        ]

        self.logger.debug(f"Node slot names: {self.node_config_slot_names}")
        self.logger.debug(f"Extra slots: {self.total_extra_slots}")
        self.logger.debug(f"Factors: {self.factors}")

        # the node must be connected to at least 2 nodes, to one slot created by the
        # PieceWiseLink, and to the extra slot created by the MultiSplitLink
        edge_counter_message = None
        if self.total_edges == 0:
            edge_counter_message = "The node must be connected to at least 2 nodes"
        elif self.total_edges == 1:
            edge_counter_message = "The extra slot created by this node is not "
            edge_counter_message += "connected to any other node. If you are "
            edge_counter_message += "going to connect this node to just one "
            edge_counter_message += "node, you need to use the 'Piece Wise Link'"

        # Total edges label
        edge_layout = QVBoxLayout()
        edge_layout.setContentsMargins(0, 0, 0, 0)
        edge_counter = QLabel(f"{self.total_edges} node(s)")
        if self.total_edges:
            edge_counter.setToolTip(", ".join(self.target_nodes))
        edge_layout.addWidget(QLabel("Connected to"))
        edge_layout.addWidget(edge_counter)

        # Extra slot counter
        extra_slots_layout = QVBoxLayout()
        extra_slots_layout.setContentsMargins(0, 0, 0, 0)
        extra_slot_count = QLabel(str(self.total_extra_slots))
        extra_slots_layout.addWidget(QLabel("Extra slots"))
        extra_slots_layout.addWidget(extra_slot_count)

        # Message
        message = QLabel()
        message.setObjectName("edge_warning_message")
        message.setWordWrap(True)
        message.setStyleSheet(f"font-size:12px;color:{Color('amber', 600).hex};")
        if edge_counter_message:
            self.logger.debug(edge_counter_message)
            message.setText(edge_counter_message)
        else:
            message.setHidden(True)

        # Counters layout
        counter_layout = QHBoxLayout()
        counter_layout.addLayout(edge_layout)
        counter_layout.addLayout(extra_slots_layout)

        # Counter + message layout
        counter_message_layout = QVBoxLayout()
        counter_message_layout.addLayout(counter_layout)
        counter_message_layout.addWidget(message)

        # Add slots
        slot_map, factor_map, warning_message = self.sanitise()
        self.logger.debug(f"Slot map is: {slot_map}")
        self.logger.debug(f"Factor map is: {factor_map}")

        # Table
        self.model = SlotsTableModel(slot_map=slot_map, factor_map=factor_map)
        # noinspection PyUnresolvedReferences
        self.model.dataChanged.connect(self.form.on_field_changed)
        # noinspection PyUnresolvedReferences
        self.model.layoutChanged.connect(self.form.on_field_changed)

        self.slot_table = TableView(model=self.model)
        self.slot_table.horizontalHeader().show()
        self.slot_table.verticalHeader().show()
        self.slot_table.setColumnWidth(0, 240)
        self.slot_table.setColumnWidth(1, 150)
        self.slot_table.setMaximumHeight(150)
        self.slot_table.setSelectionMode(TableView.SelectionMode.SingleSelection)

        if warning_message:
            self.field.set_warning(warning_message)

        # disable table if node is not properly connected or slots are wrong
        if edge_counter_message or not slot_map:
            self.slot_table.setEnabled(False)

        # Buttons
        button_layout = QHBoxLayout()
        self.move_up = PushIconButton(
            icon=qta.icon("msc.chevron-up"), label="Move up", small=True
        )
        self.move_up.setDisabled(True)
        self.move_up.setToolTip("Move the selected slot up in the table")
        # noinspection PyUnresolvedReferences
        self.move_up.clicked.connect(self.on_move_up)

        self.move_down = PushIconButton(
            icon=qta.icon("msc.chevron-down"), label="Move down", small=True
        )
        self.move_down.setDisabled(True)
        self.move_down.setToolTip("Move the selected slot down in the table")
        # noinspection PyUnresolvedReferences
        self.move_down.clicked.connect(self.on_move_down)

        button_layout.addStretch()
        button_layout.addWidget(self.move_up)
        button_layout.addWidget(self.move_down)

        # noinspection PyUnresolvedReferences
        self.slot_table.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )

        # Set layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(counter_message_layout)
        layout.addWidget(self.slot_table)
        layout.addLayout(button_layout)

    @Slot()
    def on_selection_changed(self) -> None:
        """
        Enable or disable action buttons based on the number of selected items.
        :return: None
        """
        self.logger.debug(
            f"Running on_selection_changed Slot from {get_signal_sender(self)}"
        )
        selection = self.slot_table.selectionModel().selection()
        total_rows = self.model.rowCount()

        # enable the sorting buttons only when one item is selected
        if len(selection.indexes()) == 1:
            # enable/disable sorting buttons based on the selected row (for example,
            # if last row, move down button is disabled)
            selected_row = selection.indexes()[0].row() + 1
            self.move_up.setEnabled(selected_row != 1)
            self.move_down.setEnabled(selected_row != total_rows)
        else:
            self.move_up.setEnabled(False)
            self.move_down.setEnabled(False)

    @Slot()
    def on_move_up(self) -> None:
        """
        Moves a parameter up in the table.
        :return: None
        """
        self.logger.debug(f"Running on_move_up Slot from {get_signal_sender(self)}")
        move_row(
            widget=self.slot_table,
            direction="up",
            callback=self.move_row_in_model,
        )

    @Slot()
    def on_move_down(self) -> None:
        """
        Moves a parameter down in the table.
        :return: None
        """
        self.logger.debug(f"Running on_move_down Slot from {get_signal_sender(self)}")
        move_row(
            widget=self.slot_table,
            direction="down",
            callback=self.move_row_in_model,
        )

    def move_row_in_model(self, current_index: int, new_index: int) -> None:
        """
        Moves a model's item.
        :param current_index: The row index being moved.
        :param new_index: The row index the item is being moved to.
        :return: None
        """
        self.model.nodes.insert(new_index, self.model.nodes.pop(current_index))
        self.model.slot_names.insert(
            new_index, self.model.slot_names.pop(current_index)
        )
        self.model.factors.insert(new_index, self.model.factors.pop(current_index))

    def sanitise(
        self,
    ) -> tuple[dict[str, int | str], dict[str, int | float | str], str | None]:
        """
        Sanitises the node configuration values.
        :return: A tuple with the data to use to populate the nodes/slot names
        table, factors and a warning message in case of invalid data.
        """
        warning_message = None

        # do not fill table if slots names are wrong
        if (
            # missing slot names in the node dictionary
            len(self.node_config_slot_names) != self.total_edges
            # wrong type of slot names in the node dictionary
            or not all([isinstance(s, (int, str)) for s in self.node_config_slot_names])
            # some slot names are not provided in the edges
            or not all([isinstance(s, (int, str)) for s in self.edge_slot_names])
        ):
            # fill table with empty slot names
            slot_map = {name: None for name in self.target_nodes}
            factor_map = {name: None for name in self.target_nodes}
            warning_message = (
                "The slot names are not properly configured for this node. All nodes, "
                "this node is  connected to, must have a slot name set. The slot "
                "name can be an integer or a string to let Pywr correctly connect "
                "this node to other nodes in the network"
            )
            self.logger.debug("Slots are not properly configured")
        else:
            # collect the names, the target nodes and factors - ensure proper name order
            slot_map = {}
            factor_map = {}
            for si, slot_name in enumerate(self.node_config_slot_names):
                self.logger.debug(f"Processing slot '{slot_name}'")
                # get name in edge to fetch the target node
                try:
                    ei = self.edge_slot_names.index(slot_name)
                except ValueError:
                    self.logger.debug("No slot found")
                    # let user update slot_names
                    self.form.save_button.setEnabled(True)

                    warning_message = (
                        f"The slot named '{slot_name}', set in the configuration for "
                        "for this node, does not match any slot names the node is "
                        "connected to"
                    )
                    continue
                else:
                    # get node name
                    node_name = self.target_nodes[ei]
                    self.logger.debug(f"Found {node_name} linked to provided slot")
                    slot_map[node_name] = slot_name

                    # get factor for node/slot pair
                    try:
                        if isinstance(self.factors[si], (int, float)):
                            factor_map[node_name] = self.factors[si]
                        else:
                            self.logger.debug("Factor is not a valid number")
                            factor_map[node_name] = None
                        self.logger.debug(f"Using factor {self.factors[si]}")
                    except IndexError:
                        factor_map[node_name] = None
                        self.logger.debug("Factor not found")
                        pass

            # get difference of targets and slot_map.keys() to append nodes
            # w/o slot name assigned
            missing_nodes = set(self.target_nodes).difference(list(slot_map.keys()))
            self.logger.debug(f"Appending nodes without a valid slot: {missing_nodes}")
            for node in missing_nodes:
                slot_map[node] = None
                factor_map[node] = None

        return slot_map, factor_map, warning_message

    def validate(self, name: str, label: str, value: Any) -> Validation:
        """
        Checks that the slot names are set for all target nodes.
        :param name: The field name.
        :param label: The field label.
        :param value: The field value. This is not used.
        :return: The form validation instance.
        """
        # skip validation if node is not connected
        # noinspection PyUnresolvedReferences
        if self.slot_table.isEnabled():
            if any([name is None for name in self.model.slot_names]):
                return Validation("You must define a slot name for all the nodes")

        return Validation()

    def get_value(self) -> dict[str, Any] | None:
        """
        Returns the dictionary with the following keys: self.total_extra_slots,
        slot_names, factors and target_nodes.
        :return: The values as dictionary.
        """
        # do not export the field data if the node is not connected
        if not self.slot_table.isEnabled():
            return None

        # factors can be all None
        factors = self.model.factors
        if all([f is None for f in factors]):
            factors = None

        return {
            "extra_slots": self.total_extra_slots,
            "slot_names": self.model.slot_names,
            "target_nodes": self.model.nodes,
            "factors": factors,
        }

    def unpack_from_data_helper(self, form_dict: dict) -> None:
        """
        Helper function to unpack the widget values when the form is saved.
        :param form_dict: The form dictionary.
        :return: None
        """
        self.logger.debug("Unpacking values in form dictionary")
        if self.name in form_dict:
            for key, value in form_dict[self.name].items():
                if value and key != "target_nodes":
                    self.logger.debug(f"Unpacking {key}: {value}")
                    form_dict[key] = value
                else:
                    self.logger.debug(f"Ignoring {key}")

            del form_dict[self.name]

    def updated_slot_names_in_edge_helper(self) -> None:
        """
        Updates the slot names in the "edges" when the form is saved.
        :return: None
        """
        source_node = self.value.name
        widget_data = self.get_value()
        for target_node, slot_name in zip(
            widget_data["target_nodes"], widget_data["slot_names"]
        ):
            self.logger.debug(
                f"Setting slot name to {slot_name} for {source_node}-{target_node}"
            )
            self.form: "NodeDialogForm"
            self.form.model_config.edges.set_slot(
                source_node_name=source_node,
                target_node_name=target_node,
                # node is source
                slot_pos=1,
                slot_name=slot_name,
            )
