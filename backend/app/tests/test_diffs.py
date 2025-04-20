import unittest
import json
from typing import Dict, Any
from copy import deepcopy, copy

from app.core.uqo import UQOHoraireService
from app.core.diffs import CoursDiffer
from app.models import Cours
from app.schemas.enums import ChangeType, ActiviteType, Campus


class TestCoursDiffer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the test data
        with open("app/tests/files/small_response.json", "r", encoding="utf-8") as f:
            cls.test_data = json.load(f)

        # Initialize the parser
        cls.parser = UQOHoraireService

        # Parse the first course as our base
        cls.base_course = cls.parser._parse_course(cls.test_data[1])

    def setUp(self):
        # Create fresh copies for each test
        with open("app/tests/files/small_response.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)
        self.base_course = self.parser._parse_course(test_data[1])
        self.test_data = test_data  # Store for create_modified_course

    def create_modified_course(self, modifications: Dict[str, Any]) -> Cours:
        """Helper to create a modified course with specific changes."""
        "LstActCrs.0.CollActCrsHor"
        modified_data = deepcopy(self.test_data[1])
        for key_path, value in modifications.items():
            keys = key_path.split(".")
            obj = modified_data
            for key in keys[:-1]:
                if key.isdigit():
                    obj = obj[int(key)]
                else:
                    obj = obj[key]
            obj[keys[-1]] = value
        return self.parser._parse_course(modified_data)

    def test_no_changes(self):
        """Test that identical courses show no differences."""
        dcopy = copy(self.base_course)
        differ = CoursDiffer(self.base_course, dcopy)
        diffs = differ.compare()

        # No differences should be detected
        self.assertEqual(diffs.change["change_type"], ChangeType.UNCHANGED)
        self.assertEqual(diffs.change["value"], {})

    def test_basic_attribute_changes(self):
        """Test changes to sigle, titre, and cycle."""
        modified = self.create_modified_course(
            {"SigCrs": "MOD123", "TitreCrs": "Modified Title", "CdCyc": "2"}
        )

        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # Check basic attribute changes
        self.assertEqual(
            diffs.change["value"],
            {
                "sigle": {"old": "INF1573", "new": "MOD123"},
                "titre": {"old": "Programmation II", "new": "Modified Title"},
                "cycle": {"old": 1, "new": 2},
            },
        )

        # No seance changes expected
        for seance in diffs.seance:
            self.assertEqual(seance.change["change_type"], ChangeType.UNCHANGED)

    def test_seance_added(self):
        """Test when a new seance is added."""
        # Create a modified course with an additional seance
        modified_data = deepcopy(self.test_data[1])
        new_seance = deepcopy(modified_data["LstActCrs"][0])
        new_seance["Gr"] = "99"  # New group number
        modified_data["LstActCrs"].append(new_seance)

        modified = self.parser._parse_course(modified_data)
        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # Should detect one added seance

        added_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.ADDED
        ]
        removed_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.REMOVED
        ]
        modified_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(1, len(added_seance))
        self.assertEqual(0, len(removed_seance))
        self.assertEqual(0, len(modified_seance))

        self.assertEqual(added_seance[0].groupe, "99")

    def test_seance_removed(self):
        """Test when a seance is removed."""
        # Create a modified course with one seance removed
        modified_data = deepcopy(self.test_data[1])
        modified_data["LstActCrs"] = modified_data["LstActCrs"][
            :1
        ]  # Keep only first seance

        modified = self.parser._parse_course(modified_data)
        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # # Should detect one removed seance
        added_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.ADDED
        ]
        removed_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.REMOVED
        ]
        modified_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(0, len(added_seance))
        self.assertEqual(1, len(removed_seance))
        self.assertEqual(0, len(modified_seance))

        self.assertEqual(removed_seance[0].groupe, "20")

    def test_seance_campus_changed(self):
        """Test when a seance's campus is modified."""
        modified = self.create_modified_course(
            {"LstActCrs.0.LblRegrLieuEnsei": " St-Jérôme (Campus de St-Jérôme)"}
        )

        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        added_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.ADDED
        ]
        removed_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.REMOVED
        ]
        modified_seance = [
            seance
            for seance in diffs.seance
            if seance.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(0, len(added_seance))
        self.assertEqual(0, len(removed_seance))
        self.assertEqual(1, len(modified_seance))

        # Should detect one modified seance with campus change

        self.assertEqual(
            modified_seance[0].change["value"],
            {"campus": {"old": [Campus.gat], "new": [Campus.stj]}},
        )

    def test_activite_added(self):
        """Test when an activity is added to a seance."""
        # Create a new activity
        new_activite = {
            "CdLieuEnseiAttrib": "BRAUL",
            "CdModeEnsei": "PRES",
            "CdTypeHor": "HEBDO",
            "LblTypeHor": "Hebdomadaire",
            "HrsDHor": "1400",
            "HrsFHor": "1600",
            "JourSem": "mardi",
            "LblDescAct": "Travaux dirigés",
            "LblPrea": None,
            "NbrInscMax": 0,
            "NbrInscTot": 0,
            "NbrJrInc": 7,
            "NoLocalAttrib": "A9999",
            "DateDHor": "2025-01-15T00:00:00",
            "DateFHor": "2025-04-23T00:00:00",
            "DateDHorAff": "15 janvier 2025",
            "DateFHorAff": "23 avril 2025",
            "HrsDHorAff": "14 h",
            "HrsFHorAff": "16 h",
            "R": {},
        }

        modified = self.create_modified_course(
            {
                "LstActCrs.0.CollActCrsHor": [
                    *self.test_data[1]["LstActCrs"][0]["CollActCrsHor"],
                    new_activite,
                ]
            }
        )

        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # Should detect one modified seance with one added activity
        added_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.ADDED
        ]
        removed_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.REMOVED
        ]
        modified_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(1, len(added_activite))
        self.assertEqual(0, len(removed_activite))
        self.assertEqual(0, len(modified_activite))

        added_activite[0]
        self.assertEqual(added_activite[0].change["value"], {})
        self.assertEqual(added_activite[0].type, ActiviteType.TD)
        self.assertEqual(added_activite[0].hr_debut, 1400)
        self.assertEqual(added_activite[0].hr_fin, 1600)

    def test_activite_removed(self):
        """Test when an activity is removed from a seance."""
        # Remove the first activity
        modified = self.create_modified_course(
            {
                "LstActCrs.0.CollActCrsHor": self.test_data[1]["LstActCrs"][0][
                    "CollActCrsHor"
                ][1:]
            }
        )

        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # Should detect one modified seance with one removed activity
        added_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.ADDED
        ]
        removed_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.REMOVED
        ]
        modified_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(0, len(added_activite))
        self.assertEqual(1, len(removed_activite))
        self.assertEqual(0, len(modified_activite))

    def test_activite_modified(self):
        """Test when an activity's properties are modified."""
        modified = self.create_modified_course(
            {
                "LstActCrs.0.CollActCrsHor.0.HrsDHor": "0900",
                "LstActCrs.0.CollActCrsHor.0.HrsFHor": "1200",
                "LstActCrs.0.CollActCrsHor.0.JourSem": "jeudi",
            }
        )

        differ = CoursDiffer(self.base_course, modified)
        diffs = differ.compare()

        # Should detect one removed activity and one added activity because we cannot know if it was removed or modified
        added_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.ADDED
        ]
        removed_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.REMOVED
        ]
        modified_activite = [
            activite
            for activite in diffs.seance[0].activite
            if activite.change["change_type"] == ChangeType.MODIFIED
        ]

        self.assertEqual(1, len(added_activite))
        self.assertEqual(1, len(removed_activite))
        self.assertEqual(0, len(modified_activite))

        # Note: Our current implementation treats any change as remove+add

        # # Verify the old and new values
        self.assertEqual(removed_activite[0].hr_debut, 830)
        self.assertEqual(removed_activite[0].hr_fin, 1130)
        self.assertEqual(removed_activite[0].jour, 3)

        self.assertEqual(added_activite[0].hr_debut, 900)
        self.assertEqual(added_activite[0].hr_fin, 1200)
        self.assertEqual(added_activite[0].jour, 4)


if __name__ == "__main__":
    unittest.main()
