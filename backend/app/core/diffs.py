from dataclasses import dataclass, asdict
from typing import Any, List

from app.models import Cours, Activite, Seance
from app.schemas.enums import ChangeType

@dataclass
class SingleDiff:
    old: Any
    new: Any

class CoursDiffer:

    def __init__(self, old: Cours, new: Cours) -> None:
        self.old = old
        self.new = new
    
    def compare(self):
        self._compare_basic_attributes()
        self._compare_seances()

        return self.old
    
    def _compare_basic_attributes(self):
        for field in ['sigle', 'titre', 'cycle']:
            old_value, new_value = getattr(self.old, field), getattr(self.new, field)
            if old_value != new_value:
                self.old.change['change_type'] = ChangeType.MODIFIED
                self.old.change['value'][field] = asdict(SingleDiff(old=old_value, new=new_value))
    
    def _compare_seances(self):

        old_seances = {seance.groupe: seance for seance in self.old.seance}
        new_seances = {seance.groupe: seance for seance in self.new.seance}

        for groupe, old_seance in old_seances.items():
            if old_seance.change.get('change_type') == ChangeType.UNCHANGED:
                old_seance.change['change_type'] = ChangeType.UNCHANGED
                old_seance.change['value'] = {}
        
            if groupe not in new_seances:
                old_seance.change["change_type"] = ChangeType.REMOVED

        for groupe, new_seance in new_seances.items():
            if groupe not in old_seances:
                new_seance.change["change_type"] = ChangeType.ADDED
                new_seance.cours = self.old
            else:
                old_seance = old_seances[groupe]
                self._compare_single_seance(old_seance, new_seance)
        
    def _compare_single_seance(self, old_seance: Seance, new_seance: Seance):
        for field in ['groupe', 'campus', 'ressource']:
            old_value = getattr(old_seance, field) 
            new_value = getattr(new_seance, field)
            if old_value != new_value:
                old_seance.change['change_type'] = ChangeType.MODIFIED
                old_seance.change['value'][field] = asdict(SingleDiff(old=old_value, new=new_value))

        self._compare_activities(old_seance.activite, new_seance.activite)

        
    def _compare_activities(self, old_activities: List[Activite], new_activities: List[Activite]):
        def get_activity_key(act: Activite):
            return (act.type, act.mode, act.jour, act.hr_debut, act.hr_fin, act.date_debut, act.date_fin)

        old_acts = {get_activity_key(act): act for act in old_activities}
        new_acts = {get_activity_key(act): act for act in new_activities}

        for key, act in old_acts.items():
            if key not in new_acts:
                act.change["change_type"] = ChangeType.REMOVED

        for key, act in new_acts.items():
            if key not in old_acts:
                act.change["change_type"] = ChangeType.ADDED
                act.seance = old_activities[0].seance

