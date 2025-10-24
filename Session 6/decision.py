# decision.py

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Tuple, Any
import re
from models import validate_input, function_schemas

class Decision():
    
    def __init__(self, response_text: str):
        self.response_text = response_text

    def get_decision(self) -> str:
        """
        Parse the LLM response and return the appropriate function name
        """
        # Convert response to lowercase for case-insensitive matching
        for line in self.response_text.split('\n'):
            line = line.strip()
            if line.startswith("FUNCTION_CALL:"):
                response_text = line
                break
        if response_text.startswith("FUNCTION_CALL:"):
            _, function_info = response_text.split(":", 1)
            parts = [p.strip() for p in function_info.split("|")]
            func_name, params = parts[0], parts[1:]
        elif response_text.startswith("FINAL_ANSWER:"):
             params=None
             func_name=None
        return func_name, params
                        
                        