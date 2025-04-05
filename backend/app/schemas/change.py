import json
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

    def dict(self, **kwargs):
        """Override dict method to ensure JSON serializable output"""
        return {
            'change_type': self.change_type.value,
            'value': self.value.model_dump() if self.value else None
        }
    
    def json(self, **kwargs):
        """Custom JSON serialization"""
        return json.dumps(self.dict(), **kwargs)
    
    @classmethod
    def model_validate_json(cls, json_data, *,strict: bool | None = None,context: Any | None = None,by_alias: bool | None = None,by_name: bool | None = None):
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            assert type(json_data) == Dict
            data: Dict = json_data
            
        # Extract change_type
        change_type = data.get('change_type')
        
        # Handle value based on the content
        value_data = data.get('value')
        value = None
        
        if value_data:
            # Determine which diff model to use based on fields
            if any(k in value_data for k in ('sigle', 'titre', 'cycle')):
                # Convert any null values to None
                diff_data = {k: v for k, v in value_data.items() if v is not None}
                value = CoursDiff(**diff_data)
            elif any(k in value_data for k in ('campus', 'groupe')):
                diff_data = {k: v for k, v in value_data.items() if v is not None}
                value = SeanceDiff(**diff_data)
            elif any(k in value_data for k in ('type', 'mode', 'jour', 'hr_debut', 'hr_fin')):
                diff_data = {k: v for k, v in value_data.items() if v is not None}
                value = ActiviteDiff(**diff_data)
        
        # Create the Change instance
        return cls(change_type=change_type, value=value)