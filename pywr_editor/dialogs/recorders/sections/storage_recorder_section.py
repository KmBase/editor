from pywr_editor.form import FieldConfig, StoragePickerWidget

from ..recorder_dialog_form import RecorderDialogForm
from .abstract_recorder_section import AbstractRecorderSection


class StorageRecorderSection(AbstractRecorderSection):
    def __init__(self, form: RecorderDialogForm, section_data: dict):
        """
        Initialises the form section for a StorageRecorder.
        :param form: The parent form.
        :param section_data: A dictionary containing data to pass to the widget.
        """
        super().__init__(
            form=form,
            section_data=section_data,
            section_fields=[
                FieldConfig(
                    name="storage",
                    label="Storage node",
                    field_type=StoragePickerWidget,
                    value=form.field_value("storage"),
                    help_text="Store the last volume of the storage node "
                    "provided above for each scenario",
                ),
            ],
        )
