# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mcp import types
from PIL import Image as PILImage
import math
import sys
import os
from dotenv import load_dotenv
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
from logger import mcp_server_logger

load_dotenv()

# Initalize google app password from environment variable
app_password = os.getenv("GOOGLE_PASS")

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()  
def add(a: int, b: int) -> int:
    """Add two numbers"""
    mcp_server_logger.info("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    mcp_server_logger.info("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    mcp_server_logger.info("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    mcp_server_logger.info("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    mcp_server_logger.info("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    mcp_server_logger.info("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    mcp_server_logger.info("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    mcp_server_logger.info("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    mcp_server_logger.info("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    mcp_server_logger.info("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    mcp_server_logger.info("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    mcp_server_logger.info("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    mcp_server_logger.info("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    mcp_server_logger.info("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    mcp_server_logger.info("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    mcp_server_logger.info("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    mcp_server_logger.info("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    mcp_server_logger.info("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    mcp_server_logger.info("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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
# DEFINE RESOURCES

@mcp.tool()
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
        msg["Subject"] = "MCP email tool sent this mail | EAG V2 Assignment 4"

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
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    mcp_server_logger.info("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    mcp_server_logger.info("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
