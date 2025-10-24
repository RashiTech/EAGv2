"""
Action Layer - Task Execution Module
==================================

This layer handles the execution of specific tasks including:
1. Mathematical operations (ASCII conversion, exponential sums)
2. Paint interactions (open, draw rectangle, add text)
3. Email sending
4. Utility functions (calculations, verifications)

Each function supports validation of inputs/outputs using Pydantic models.
Paint operations use pywinauto for GUI automation.
"""

from typing import Dict, Any, Union, Optional, Tuple, List
import math
import time
import os
import json
import asyncio
import subprocess
import win32gui
import win32con
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto import mouse, findwindows
from pywinauto.controls.hwndwrapper import HwndWrapper
import logging

from models import validate_input, validate_output, function_schemas
from logger import mcp_server_logger
import inspect


# Gmail configuration
app_password = os.getenv('GMAIL_APP_PASSWORD')  # App-specific password

# Global paint instance
paint_app = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextContent:
    """Response content wrapper with type information."""
    def __init__(self, text: str, type: str = "text"):
        self.type = type
        self.text = text
        
    def __repr__(self):
        return f"{self.type}: {self.text}"
    
    @staticmethod
    def create(text: str) -> 'TextContent':
        """Helper to create a TextContent with default type."""
        return TextContent(text=str(text))

class Action:
    def __init__(self):
        # Map tool names to bound methods so they can be called from an Action instance
        self.func_map = {
            'add': self.add,
            'add_list': self.add_list,
            'subtract': self.subtract,
            'multiply': self.multiply,
            'divide': self.divide,
            'power': self.power,
            'sqrt': self.sqrt,
            'cbrt': self.cbrt,
            'factorial': self.factorial,
            'log': self.log,
            'remainder': self.remainder,
            'sin': self.sin,
            'cos': self.cos,
            'tan': self.tan,
            'strings_to_chars_to_int': self.strings_to_chars_to_int,
            'int_list_to_exponential_sum': self.int_list_to_exponential_sum,
            'fibonacci_numbers': self.fibonacci_numbers,
            'show_reasoning': self.show_reasoning,
            'calculate': self.calculate,
            'verify': self.verify,
            'draw_rectangle': self.draw_rectangle,
            'add_text_in_paint': self.add_text_in_paint,
            'open_paint': self.open_paint,
            'send_email': self.send_email,
        }

    async def act(self, func_name: str, params: Union[List[Any], Dict[str, Any]]) -> Any:
        """Execute a tool by name with the given parameters.
        
        Args:
            func_name: Name of the tool to execute (must be in func_map)
            params: List of parameters or dictionary of named parameters
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If tool doesn't exist or parameters are invalid
        """
        try:
            # Find the matching tool
            tool = self.func_map.get(func_name)
            if not tool:
                logger.info(f"DEBUG: Available tools: {list(self.func_map.keys())}")
                raise ValueError(f"Unknown tool: {func_name}")

            # Get function signature
            sig = inspect.signature(tool)
            arguments = {}
            
            # Handle parameters based on their type
            if isinstance(params, dict):
                # Dictionary params - use as is after validation
                for name, value in params.items():
                    if name not in sig.parameters:
                        raise ValueError(f"Unknown parameter {name} for {func_name}")
                    arguments[name] = value
            else:
                # List params - map to parameter names in order
                param_names = [name for name in sig.parameters 
                             if name != 'self']
                
                if len(params) != len(param_names):
                    raise ValueError(
                        f"Expected {len(param_names)} parameters for {func_name}, got {len(params)}")
                
                for name, value in zip(param_names, params):
                    # Handle list parameters - if value looks like a list string
                    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                        try:
                            # Convert string list "[1,2,3]" to actual list
                            clean_list = value.strip('[]')
                            if clean_list:  # Only split if not empty
                                value = [item.strip().strip("'\"") for item in clean_list.split(',')]
                            else:
                                value = []
                        except Exception as e:
                            logger.info(f"Failed to parse list parameter: {e}")
                    arguments[name] = value
                
                # # Convert the value to the correct type based on the schema
                # if param_type == 'integer':
                #     arguments[param_name] = int(value)
                # elif param_type == 'number':
                #     arguments[param_name] = float(value)
                # elif param_type == 'array':
                #     # Handle array input
                #     if isinstance(value, str):
                #         value = value.strip('[]').split(',')
                #     arguments[param_name] = [int(x.strip()) for x in value]
                # else:
                #     arguments[param_name] = str(value)

            logger.info(f"DEBUG: Final arguments: {arguments}")
            logger.info(f"DEBUG: Calling tool {func_name}")
            # Call async tools with await; run sync tools in a thread pool so the event loop is not blocked.
            try:
                if asyncio.iscoroutinefunction(tool):
                    result = await tool(**arguments)
                else:
                    loop = asyncio.get_running_loop()
                    maybe = await loop.run_in_executor(None, lambda: tool(**arguments))
                    # If a sync tool unexpectedly returned a coroutine, await it.
                    if asyncio.iscoroutine(maybe):
                        result = await maybe
                    else:
                        result = maybe
                    return result             
            except Exception as e:
                logger.exception(f"Error while calling tool {func_name}")
                raise
            # result = await session.call_tool(func_name, arguments=arguments)
        except Exception as e:
            logger.exception(f"Error in act method for tool {func_name}: {str(e)}")
            raise
            
        # Paint window handling
    @staticmethod
    async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
        """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
        global paint_app
        try:
            if not paint_app:
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text="Paint is not open. Please call open_paint first."
                        )
                    ]
                }
            
            # Get the Paint window
            paint_window = paint_app.window(class_name='MSPaintApp')
            
            # Get primary monitor width to adjust coordinates
            # primary_width = GetSystemMetrics(0)
            # print(primary_width)
            
            # Ensure Paint window is active
            if not paint_window.has_focus():
                paint_window.set_focus()
                time.sleep(1.5)
            
            # paint_window.type_keys('r')  # Select rectangle tool 
            # paint_window.type_keys('r')  # Select rectangle tool
            # time.sleep(0.8)
            # Click on the Rectangle tool using the correct coordinates for secondary screen

            paint_window.click_input(coords=(661, 102 ))
            time.sleep(2.1)
            

            
            # print({"message": "input clicked"})

            # Get the canvas area
            # canvas = paint_window.child_window(class_name='MSPaintView')
            canvas = paint_window.child_window(class_name='MSPaintView', found_index=0)
            if not canvas.exists():
                for child in paint_window.descendants():
                    print(f"Descendant: class={child.friendly_class_name()}, handle={child.handle}, text={child.window_text()}")
            # paint_window.click_input(coords=(607, 102 ))
            # time.sleep(1.9)

            canvas_rect = canvas.rectangle()
            # print(canvas_rect)
            # Draw within canvas bounds

            canvas.press_mouse_input(coords=(x1, y1))
            time.sleep(2.1)

            # start = (canvas_rect.left + 607, canvas_rect.top + 425)
            # end = (canvas_rect.left + 940, canvas_rect.top + 619)


            # canvas.press_mouse_input(coords=start)
            # time.sleep(0.3)
            # canvas.move_mouse_input(coords=end)
            # time.sleep(0.3)
            # canvas.release_mouse_input(coords=end)
            # sys.stdout.flush()

            # # Use relative coordinates within canvas
            canvas.press_mouse_input(coords=(x1, y1))
            time.sleep(1.9)
            canvas.move_mouse_input(coords=(x2, y2))
            time.sleep(1.9)
            canvas.release_mouse_input(coords=(x2, y2))
            time.sleep(1.9)

            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                    )
                ]
            }
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error drawing rectangle: {str(e)}"
                    )
                ]
            }

    @staticmethod
    async def add_text_in_paint(text: str) -> dict:
        """Add text in Paint"""
        global paint_app
        try:
            if not paint_app:
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text="Paint is not open. Please call open_paint first."
                        )
                    ]
                }
            
            # Get the Paint window
            paint_window = paint_app.window(class_name='MSPaintApp')
            paint_window.set_focus()
            time.sleep(2)

            # Print all descendants for debugging
            for desc in paint_window.descendants():
                print(f"Descendant: {desc.window_text()} | Class: {desc.friendly_class_name()}")

            # Try to find the canvas by class name or index
            canvas = paint_window.child_window(class_name='MSPaintView')
            if not canvas.exists():
                canvas = paint_window.child_window(found_index=0)
            
            paint_window.type_keys('t')
            time.sleep(1.5)
            paint_window.type_keys('x')
            time.sleep(1.5)
            
            # Click where to start typing
            canvas.click_input(coords=(627, 435))
            time.sleep(1.5)
            
            # Type the text passed from client
            paint_window.type_keys(text)
            time.sleep(1.5)
            
            # Click to exit text mode
            canvas.click_input(coords=(827, 435))
            time.sleep(1.5)

            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Text:'{text}' added successfully"
                    )
                ]
            }
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
            }

    @staticmethod
    async def open_paint() -> dict:
        """Open Microsoft Paint maximized on primary monitor"""
        global paint_app
        try:
            paint_app = Application().start('mspaint.exe')
            time.sleep(0.2)
            
            # Get the Paint window
            paint_window = paint_app.window(class_name='MSPaintApp')
            
            # Get primary monitor width
            # primary_width = GetSystemMetrics(0)
            primary_width = 0
            
            # First move to secondary monitor without specifying size
            win32gui.SetWindowPos(
                paint_window.handle,
                win32con.HWND_TOP,
                primary_width + 1, 0,  # Position it on secondary monitor
                0, 0,  # Let Windows handle the size
                win32con.SWP_NOSIZE  # Don't change the size
            )
            
            # Now maximize the window
            win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
            time.sleep(0.2)
            
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint opened successfully on primary monitor and maximized"
                    )
                ]
            }
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error opening Paint: {str(e)}"
                    )
                ]
            }
    # Math and utility functions
    @staticmethod
    def add(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Add two numbers together.
        
        Args:
            a: First number (will be converted to int)
            b: Second number (will be converted to int)
            
        Returns:
            Sum of a and b as integer
        """
        return int(a) + int(b)

    @staticmethod
    def add_list(numbers: List[Union[int, float, str]]) -> int:
        """Calculate the sum of a list of numbers.
        
        Args:
            numbers: List of numbers to sum (each will be converted to int)
            
        Returns:
            Sum of all numbers as integer
        """
        return sum(map(int, numbers))

    @staticmethod
    def subtract(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Subtract b from a.
        
        Args:
            a: Number to subtract from (will be converted to int)
            b: Number to subtract (will be converted to int)
            
        Returns:
            Difference a - b as integer
        """
        return int(a) - int(b)

    @staticmethod
    def multiply(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Multiply two numbers.
        
        Args:
            a: First number (will be converted to int)
            b: Second number (will be converted to int)
            
        Returns:
            Product of a and b as integer
        """
        return int(a) * int(b)

    @staticmethod
    def divide(a: Union[int, float, str], b: Union[int, float, str]) -> float:
        """Divide a by b.
        
        Args:
            a: Numerator (will be converted to float)
            b: Denominator (will be converted to float, must not be zero)
            
        Returns:
            Quotient a / b as float
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        return float(a) / float(b)

    @staticmethod
    def power(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Raise a to the power of b.
        
        Args:
            a: Base (will be converted to int)
            b: Exponent (will be converted to int)
            
        Returns:
            a ^ b as integer
        """
        return int(a) ** int(b)

    @staticmethod
    def sqrt(a: Union[int, float, str]) -> float:
        """Calculate the square root.
        
        Args:
            a: Non-negative number (will be converted to float)
            
        Returns:
            Square root of a as float
            
        Raises:
            ValueError: If a is negative
        """
        a = float(a)
        if a < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return a ** 0.5

    @staticmethod
    def cbrt(a: Union[int, float, str]) -> float:
        """Calculate the cube root.
        
        Args:
            a: Number (will be converted to float)
            
        Returns:
            Cube root of a as float
        """
        return float(a) ** (1/3)

    @staticmethod
    def factorial(a: Union[int, float, str]) -> int:
        """Calculate factorial.
        
        Args:
            a: Non-negative integer (will be converted to int)
            
        Returns:
            a! (factorial of a) as integer
            
        Raises:
            ValueError: If a is negative
        """
        a = int(a)
        if a < 0:
            raise ValueError("Factorial not defined for negative numbers")
        return math.factorial(a)

    @staticmethod
    def log(a: Union[int, float, str]) -> float:
        """Calculate natural logarithm.
        
        Args:
            a: Positive number (will be converted to float)
            
        Returns:
            Natural log of a as float
            
        Raises:
            ValueError: If a is not positive
        """
        a = float(a)
        if a <= 0:
            raise ValueError("Cannot calculate log of non-positive number")
        return math.log(a)

    @staticmethod
    def remainder(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Calculate remainder of division.
        
        Args:
            a: Dividend (will be converted to int)
            b: Divisor (will be converted to int, must not be zero)
            
        Returns:
            Remainder of a / b as integer
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        return int(a) % int(b)

    @staticmethod
    def sin(a: Union[int, float, str]) -> float:
        """Calculate sine of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Sine of a as float
        """
        return math.sin(float(a))

    @staticmethod
    def cos(a: Union[int, float, str]) -> float:
        """Calculate cosine of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Cosine of a as float
        """
        return math.cos(float(a))

    @staticmethod
    def tan(a: Union[int, float, str]) -> float:
        """Calculate tangent of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Tangent of a as float
        """
        return math.tan(float(a))

    @staticmethod
    def mine(a, b):
        return int(a) - int(b) - int(b)

    @staticmethod
    def strings_to_chars_to_int(text: str) -> List[int]:
        """Convert a string to a list of ASCII values.
        
        Args:
            text: The input string to convert to ASCII values
            
        Returns:
            List of integer ASCII values for each character
        """
        return [ord(char) for char in text]

    @staticmethod
    def int_list_to_exponential_sum(int_list: Union[List[Union[int, str]], str]) -> float:
        """Calculate sum of exponentials of integers in the list.
        
        Args:
            int_list: List of integers or string representation of a list
            
        Returns:
            Sum of e^x for each x in the list
            
        Raises:
            ValueError: If input can't be converted to list of integers
        """
        # Handle string input
        if isinstance(int_list, str):
            if int_list.startswith('[') and int_list.endswith(']'):
                # Parse string list "[1,2,3]" format
                clean_list = int_list.strip('[]')
                if clean_list:
                    int_list = [item.strip().strip("'\"") for item in clean_list.split(',')]
                else:
                    int_list = []
            else:
                raise ValueError("String input must be in list format [x,y,z]")
                
        # Convert all items to int and calculate sum
        return sum(math.exp(int(i)) for i in int_list)

    @staticmethod
    def fibonacci_numbers(n):
        n = int(n)
        if n <= 0:
            return []
        fib_sequence = [0, 1]
        for _ in range(2, n):
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return fib_sequence[:n]

    @staticmethod
    def show_reasoning(steps):
        """Show reasoning steps, handling both list and string inputs.
        
        Args:
            steps: Either a list of steps or a string containing steps separated by periods
                  or semicolons.
        """
        print("Reasoning steps:")
        if isinstance(steps, str):
            # Split on either periods or semicolons, handle both delimiters
            if ';' in steps:
                steps_list = [s.strip() for s in steps.split(';') if s.strip()]
            else:
                steps_list = [s.strip() for s in steps.split('.') if s.strip()]
        else:
            steps_list = steps
            
        for i, step in enumerate(steps_list, 1):
            print(f"Step {i}: {step}")
        return "Reasoning shown"

    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate result of a mathematical expression.
        
        Args:
            expression: String containing a valid Python math expression
            
        Returns:
            String representation of result or error message
        """
        try:
            result = eval(expression)
            print(f"Result: {result}")
            return str(result)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def verify(expression: str, expected: Union[int, float, str]) -> str:
        """Verify if an expression evaluates to expected value.
        
        Args:
            expression: String containing a valid Python math expression
            expected: Expected result (will be converted to float)
            
        Returns:
            "True" if equal within tolerance, "False" otherwise
        """
        try:
            actual = float(eval(expression))
            is_correct = abs(actual - float(expected)) < 1e-10
            print(f"Verify: {expression} == {expected} ? {is_correct}")
            return str(is_correct)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    async def send_email(text: str) -> dict:
        """Send email with the text content"""
        try:

            # Gmail account details
            sender_email = "rashi.ai2022@gmail.com"
            receiver_email = "rashi.ai2022@gmail.com"

            # Create email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = "Email tool sent via Action Module | EAG V2 Assignment 6"

            # Body of the email
            body = f"Hello, this is final answer to your question: {text}"
            msg.attach(MIMEText(body, "plain"))

            # Send email via Gmail's SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(msg)

            mcp_server_logger.info(f"Email sent successfully with content {text}")
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Email sent successfully!"
                    )
                ]
            }
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error sending mail: {str(e)}"
                    )
                ]
            }
        
    @staticmethod
    def show_reasoning(steps):
        """Show the step-by-step reasoning process.
        
        Args:
            steps: Either a list of steps or a string containing steps separated by
                  periods or semicolons.
        """
        print("\n=== Reasoning Steps ===")
        
        if isinstance(steps, str):
            # Split on either periods or semicolons, handle both delimiters
            if ';' in steps:
                steps_list = [s.strip() for s in steps.split(';') if s.strip()]
            else:
                steps_list = [s.strip() for s in steps.split('.') if s.strip()]
        else:
            steps_list = steps
            
        for i, step in enumerate(steps_list, 1):
            print(f"\nStep {i}:")
            print(f"  {step}")
            
        return "Reasoning shown"


    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate the result of an expression"""
        print("\n=== Calculate ===")
        print(f"Expression: {expression}")
        try:
            result = eval(expression)
            print(f"Result: {result}")
            return str(result)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def verify(expression: str, expected: float) -> str:
        """Verify if a calculation is correct"""
        print("\n=== Verify ===")
        print(f"Checking: {expression} = {expected}")
        try:
            actual = float(eval(expression))
            is_correct = abs(actual - float(expected)) < 1e-10
            
            if is_correct:
                print(f"✓ Correct! {expression} = {expected}")
            else:
                print(f"✗ Incorrect! {expression} should be {actual}, got {expected}")
                
            return str(is_correct)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

        
            
