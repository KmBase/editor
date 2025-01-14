from pywr_editor.form import (
    FieldConfig,
    FormSection,
    ParameterLineEditWidget,
    TableValuesWidget,
    Validation,
)

from ..parameter_dialog_form import ParameterDialogForm


class PiecewiseIntegralParameterSection(FormSection):
    def __init__(self, form: ParameterDialogForm, section_data: dict):
        """
        Initialise the form section for PiecewiseIntegralParameter.
        :param form: The parent form.
        :param section_data: A dictionary containing data to pass to the widget.
        """
        super().__init__(form, section_data)
        self.form: ParameterDialogForm

        self.add_fields(
            {
                "Configuration": [
                    FieldConfig(
                        # this field includes both x and y values
                        name="x_y_values",
                        label="Piecewise function",
                        field_type=TableValuesWidget,
                        field_args={"min_total_values": 2},
                        validate_fun=self._check_x,
                        value={
                            "x": self.form.field_value("x"),
                            "y": self.form.field_value("y"),
                        },
                        help_text="Integrate the piecewise function between 0 and the "
                        "value given by the parameter provided below. The values of x "
                        "must be monotonically increasing and greater than zero",
                    ),
                    FieldConfig(
                        name="parameter",
                        field_type=ParameterLineEditWidget,
                        value=self.form.field_value("parameter"),
                        help_text="The parameter that defines the upper boundary limit "
                        "of the integration",
                    ),
                ],
                "Miscellaneous": [self.form.comment],
            }
        )

    @staticmethod
    def _check_x(
        name: str, label: str, value: dict[str, list[float | int]]
    ) -> Validation:
        """
        Checks that "x" is monotonically increasing and larger than zero
        :param name: The field name.
        :param label: The field label.
        :param value: The field value.
        :return: The validation instance.
        """
        x = value["x"]
        if any([j - i <= 0 for i, j in zip(x[:-1], x[1:])]):
            return Validation("The values must be strictly monotonically increasing")
        elif x[0] < 0:
            return Validation("The values must start from zero")

        return Validation()

    def filter(self, form_data: dict) -> None:
        """
        Splits the data points dictionary.
        :param form_data: The form data dictionary.
        :return: None.
        """
        # split x and y
        for var_name, var_values in form_data["x_y_values"].items():
            form_data[var_name] = var_values
        del form_data["x_y_values"]
