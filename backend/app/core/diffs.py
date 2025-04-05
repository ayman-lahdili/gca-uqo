from app.models import Cours, Activite, Seance
from pydantic import BaseModel
from typing import Any, List, Dict
from enum import Enum
from app.schemas.enums import ChangeType
from app.schemas.change import SingleDiff, ActiviteDiff, SeanceDiff, CoursDiff, Change
from app.schemas.read import CoursRead

class DiffStatus(BaseModel):
    added: List[Any] = []
    removed: List[Any] = []
    modified: List[Any] = []


class CoursDiffer:

    def __init__(self, old: Cours, new: Cours) -> None:
        self.old = old
        self.new = new
    
    def compare(self):
        self._compare_basic_attributes()
        self._compare_seances()

        return self.old
    
    def _compare_basic_attributes(self):
        self.old.change = Change(
            value=CoursDiff(
                sigle=SingleDiff(old=self.old.sigle, new=self.new.sigle),
                titre=SingleDiff(old=self.old.titre, new=self.new.titre),
                cycle=SingleDiff(old=self.old.cycle, new=self.new.cycle)
            )
        )
    
    def _compare_seances(self):
        diff_status = DiffStatus()

        old_seances = {seance.groupe: seance for seance in self.old.seance}
        new_seances = {seance.groupe: seance for seance in self.new.seance}

        for groupe, old_seance in old_seances.items():
            if groupe not in new_seances:
                old_seance.change.change_type = ChangeType.REMOVED
                diff_status.removed.append(old_seance)

        for groupe, new_seance in new_seances.items():
            if groupe not in old_seances:
                new_seance.change.change_type = ChangeType.ADDED
                new_seance.cours = self.old
                diff_status.added.append(new_seance)
            else:
                old_seance = old_seances[groupe]
                self._compare_single_seance(old_seance, new_seance)
        
    def _compare_single_seance(self, old_seance: Seance, new_seance: Seance):
        old_seance.change = Change(
            value=SeanceDiff(
                campus=SingleDiff(old=old_seance.campus, new=new_seance.campus),
                groupe=SingleDiff(old=old_seance.groupe, new=new_seance.groupe)
            )
        )

        self._compare_activities(old_seance.activite, new_seance.activite)

        
    def _compare_activities(self, old_activities: List[Activite], new_activities: List[Activite]):
        diff_status = DiffStatus()

        def get_activity_key(act: Activite):
            return (act.type, act.mode, act.jour, act.hr_debut, act.hr_fin)

        old_acts = {get_activity_key(act): act for act in old_activities}
        new_acts = {get_activity_key(act): act for act in new_activities}

        for key, act in old_acts.items():
            if key not in new_acts:
                act.change.change_type = ChangeType.REMOVED
                diff_status.removed.append(act)

        for key, act in new_acts.items():
            if key not in old_acts:
                act.change.change_type = ChangeType.ADDED
                act.seance = old_activities[0].seance
                diff_status.added.append(act)

