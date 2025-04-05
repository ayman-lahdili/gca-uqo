from pydantic import BaseModel
from typing import Any, Optional, Dict, Union, Type
from app.schemas.enums import ChangeType

class SingleDiff(BaseModel):
    old: Any
    new: Any
    
    def __new__(cls, **data):
        if 'old' in data and 'new' in data and data['old'] == data['new']:
            return None
        return super().__new__(cls)

class DiffBaseModel(BaseModel):
    def __new__(cls, **data):
        instance = super().__new__(cls)
        # Create the instance using BaseModel.__new__
        instance.__init__(**data)
        # Initialize it to populate the attributes
        
        # Check if all attributes are None
        if all(v is None for v in instance.__dict__.values()):
            return None
        return instance

class ActiviteDiff(DiffBaseModel):
    type: Optional[SingleDiff] = None
    mode: Optional[SingleDiff] = None
    jour: Optional[SingleDiff] = None
    hr_debut: Optional[SingleDiff] = None
    hr_fin: Optional[SingleDiff] = None

class SeanceDiff(DiffBaseModel):
    campus: Optional[SingleDiff] = None
    groupe: Optional[SingleDiff] = None

class CoursDiff(DiffBaseModel):
    sigle: Optional[SingleDiff] = None
    titre: Optional[SingleDiff] = None
    cycle: Optional[SingleDiff] = None

class Change(BaseModel):
    change_type: ChangeType = ChangeType.UNCHANGED
    value: Union[ActiviteDiff, SeanceDiff, CoursDiff, None] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # After initialization, check value and set change_type accordingly
        if self.value is None:
            self.change_type = ChangeType.UNCHANGED
        else:
            self.change_type = ChangeType.MODIFIED
