import maya.cmds as cmds

# Check if window exists, and delete if it does
if cmds.window("CalculatorWindow", exists=True):
    cmds.deleteUI("CalculatorWindow", window=True)

# Create the Calculator UI
def create_calculator_ui():
    # Main Window
    window = cmds.window("CalculatorWindow", title="Maya Calculator", widthHeight=(300, 200))
    cmds.columnLayout(adjustableColumn=True)
    
    # Text field to display numbers and results
    result_field = cmds.textField("resultField", text="0", editable=False, h=40)

    # Variables to store values and operations
    global first_num, second_num, operator
    first_num, second_num, operator = 0, 0, ""

    # Helper function to update the result field
    def update_result_field(value):
        cmds.textField(result_field, edit=True, text=str(value))

    # Callback functions for calculator operations
    def number_click(number):
        current = cmds.textField(result_field, query=True, text=True)
        if current == "0" or operator:
            current = ""
        update_result_field(current + str(number))

    def operator_click(op):
        global first_num, operator
        first_num = float(cmds.textField(result_field, query=True, text=True))
        operator = op
        update_result_field("")

    def calculate_result(*args):
        global first_num, second_num, operator
        second_num = float(cmds.textField(result_field, query=True, text=True))
        result = 0

        # Perform the calculation based on the operator
        if operator == "+":
            result = first_num + second_num
        elif operator == "-":
            result = first_num - second_num
        elif operator == "*":
            result = first_num * second_num
        elif operator == "/":
            result = first_num / second_num if second_num != 0 else "Error"

        # Update the display with the result
        update_result_field(result)
        # Reset operator for next calculation
        operator = ""

    def clear_result(*args):
        global first_num, second_num, operator
        first_num, second_num, operator = 0, 0, ""
        update_result_field("0")

    # Layout for calculator buttons
    cmds.gridLayout(numberOfColumns=4, cellWidthHeight=(75, 40))

    # Number buttons 1-9
    for i in range(1, 10):
        cmds.button(label=str(i), command=lambda x, i=i: number_click(i))
    
    # Zero button
    cmds.button(label="0", command=lambda x: number_click(0))

    # Operator buttons
    cmds.button(label="+", command=lambda x: operator_click("+"))
    cmds.button(label="-", command=lambda x: operator_click("-"))
    cmds.button(label="*", command=lambda x: operator_click("*"))
    cmds.button(label="/", command=lambda x: operator_click("/"))

    # Equal and Clear buttons
    cmds.button(label="=", command=calculate_result)
    cmds.button(label="C", command=clear_result)

    # Show the UI
    cmds.showWindow(window)

# Execute the function to create the calculator UI
create_calculator_ui()
