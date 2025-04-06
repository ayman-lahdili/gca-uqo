import json
from pydantic import BaseModel
from typing import Any, Optional, Dict, Union, Type
from app.schemas.enums import ChangeType

class SingleDiff(BaseModel):
    old: Any
    new: Any
