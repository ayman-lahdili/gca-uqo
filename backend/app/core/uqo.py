import requests
import re
import json
from bs4 import BeautifulSoup
import os

from typing import List, Literal, Dict, Any

from app.models import Cours, Activite, Seance
from app.schemas.enums import Campus, ActiviteType, ActiviteMode, JourSemaine, ChangeType

class UQOAPIException(Exception):
    """Custom exception for UQO API related errors."""
    pass

class UQOProgramService:
    
    DEPARTEMENT = Literal['INFOR']

    def __init__(self, debug: bool = False) -> None:
        self.debug = debug

    def get_programmes(self, departement: DEPARTEMENT) -> List[Dict[str, Any]]:
        url = "https://etudier.uqo.ca/programmes"
        pattern = re.compile(r'jsonLstRes\s*=\s*(\[.*)')

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            html_text = resp.text
        except requests.exceptions.RequestException as e:
            raise UQOAPIException(f"Failed to fetch {url}: {str(e)}")
    
        match = pattern.search(html_text)
        
        if match:
            json_string = match.group(1)[:-2]
            try:
                program_data = json.loads(json_string)
                result = [program for program in program_data if program["CdSectHtml"] == departement]
                return result
            except json.JSONDecodeError as e:
                self.__debug_parse_error(json_string, e)
                raise UQOAPIException(f"JSON parsing error: {str(e)}")
        else:
            raise UQOAPIException("Could not find the pattern 'jsonLstRes = [...]' in the response text.")

    @staticmethod
    def __debug_parse_error(json_string: str, error: json.JSONDecodeError):
        with open("debug/debug_json_string.json", "w", encoding="utf-8") as f:
            f.write(json_string)
        print(f"Successfully saved full string.")

        # Print context around the error position from the string
        error_pos = error.pos
        context_size = 60 # Show 60 chars before and after
        start_index = max(0, error_pos - context_size)
        end_index = min(len(json_string), error_pos + context_size)
        print("\n--- Problematic string context (from extracted string) ---")
        # Adding markers to pinpoint the exact error char
        print(f"...{json_string[start_index:error_pos]}<ERROR STARTS HERE>{json_string[error_pos:end_index]}...")
        print("-" * (error_pos - start_index + len("...")) + "^ ERROR POS")

class UQOCoursService:
    
    DEPARTEMENT = Literal['DII']

    def __init__(self) -> None:
        self.url = "https://etudier.uqo.ca/cours"
        self.session = requests.Session()
        self.headers = {}
        self.current_token = None
        self.fetch_new_token()

    def fetch_new_token(self):
        try:
            # First get the page to obtain fresh token
            response = self.session.get(self.url)
            
            # Extract token from cookies
            for cookie in self.session.cookies:
                if cookie.name.startswith('.AspNetCore.Antiforgery.'):
                    if cookie.value:
                        self.headers = {
                            "Cookie": cookie.name +"="+ cookie.value
                        }
                    else:
                        print('No cookie')
                    break
            
            if not self.current_token:
                soup = BeautifulSoup(response.text, 'html.parser')
                token_input: Any = soup.find('input', {'name': '__RequestVerificationToken'})
                if token_input:
                    self.current_token = token_input['value']            
        except Exception as e:
            print(f"Error refreshing token: {e}")

    def get_courses(self, departement: DEPARTEMENT, cycle: str = ""):
            
        data = {
            "CritRech": "",
            "Module": departement,
            "Cycle": cycle,
            "TypeAff": "SigCrs",
            "__RequestVerificationToken": self.current_token
        }
        
        try:
            response = self.session.post(
                self.url,
                headers=self.headers,
                data=data
            )

            return self.parse_courses_html(response.text, data)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    @staticmethod
    def parse_courses_html(html_content: str, data: Dict[str, str]) :
        print("Parsing HTML content to extract courses")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the div containing course list
        courses_div: Any = soup.find('div', id='divLstCrs')
        if not courses_div:
            print("Could not find courses div in HTML")
            return []
        
        # Find all course items (each row contains a course)
        course_items = courses_div.find_all('div', class_='row')
        
        # Skip the header row
        course_items = [item for item in course_items if 'row-entete' not in item.get('class', [])]
        
        courses = []
        for item in course_items:
            # Extract sigle
            item: Any
            sigle_tag: Any = item.find('a')
            sigle = sigle_tag.text.strip() if sigle_tag else None
            
            # Extract titre
            titre_div = item.find_all('div', class_='col-12 col-md-7 col-lg-5 order-3 order-lg-2')
            titre = titre_div[0].text.strip() if titre_div else None
            
            # Extract cycle (from badge-warning span)
            cycle_span = item.find('span', class_='badge')
            cycle = cycle_span.text.strip()[:1] if cycle_span else None
            
        
            # Extract crédits
            credits_div = item.find_all('div', class_='col-12 col-md-5 col-lg-1 text-left text-md-right text-xl-center text-xl-center order-4')
            credit = credits_div[0].text.strip().split()[0] if credits_div else None
            
            # Extract préalables (empty in this example, but would be in the last column)
            prereq_div = item.find_all('div', class_='col-12 col-lg-3 order-5')
            prereq = []
            if prereq_div:
                prereq_links = prereq_div[0].find_all('a')
                prereq = [link.text.strip() for link in prereq_links]
            
            courses.append({
                'sigle': sigle,
                'titre': titre,
                'cycle': cycle,
                'credit': credit,
                'préalable': prereq
            })
        
        return courses

class UQOHoraireService:

    def __init__(self, trimestre) -> None:
        self.url = 'https://etudier.uqo.ca/activites/recherche-horaire-resultats-ajax'
        self.trimestre = trimestre
        self.horaire = self.get_horaire(self.trimestre)

    def get_horaire(self, trimestre: int):
        params = {
            'CdTrimestre': trimestre,
            'JourSem': ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']
        }

        results = requests.get(self.url, params=params)

        return results.json()

    def get_course(self, sigle: str):
        # print(self.horaire)
        cours = None
        for cours_data in self.horaire:
            if cours_data['SigCrs'] == sigle:
                cours = self._parse_course(cours_data)
                
        return cours
    
    @staticmethod
    def _parse_course(cours: Dict[str, Any]) -> Cours:
        """Parse a course dictionary into a Cours object."""
        return Cours(
            sigle=cours['SigCrs'],
            trimestre=int(cours['CdTrimestreAct']),
            titre=cours['TitreCrs'],
            cycle=int(cours['CdCyc']),
            change={'change_type': ChangeType.UNCHANGED, 'value': {}},
            seance=[
                Seance(
                    campus=_parse_campus(seance["LblRegrLieuEnsei"]),
                    trimestre=int(cours['CdTrimestreAct']),
                    groupe=seance["Gr"],
                    change={'change_type': ChangeType.UNCHANGED, 'value': {}},
                    sigle=cours['SigCrs'],
                    activite=[
                        Activite(
                            trimestre=int(cours['CdTrimestreAct']),
                            sigle=cours['SigCrs'],
                            groupe=seance["Gr"],
                            type=ActiviteType(activite["LblDescAct"]),
                            mode=ActiviteMode(activite["CdModeEnsei"]),
                            jour=_parse_jour(activite["JourSem"]),
                            hr_debut=int(activite["HrsDHor"]),
                            hr_fin=int(activite["HrsFHor"]),
                            change={'change_type': ChangeType.UNCHANGED, 'value': {}},
                        )
                        for activite in seance["CollActCrsHor"]
                    ]
                )
                for seance in cours["LstActCrs"]
            ]
        )

def _parse_campus(unparsed: str) -> List[Campus]:
    unparsed = unparsed.strip().lower()
    campus = []
    if 'gat' in unparsed:
        campus.append(Campus.gat)
    if 'st' in unparsed:
        campus.append(Campus.stj)
    return campus

def _parse_jour(unparsed: JourSemaine):
    return {
        "lundi": 1,
        "mardi": 2,
        "mercredi": 3,
        "jeudi": 4,
        "vendredi": 5,
        "samedi": 6,
        "dimanche": 7
    }[unparsed]