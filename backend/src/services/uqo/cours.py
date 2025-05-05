import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from src.schemas.uqo import Departement, UQOCours

class UQOCoursService:
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
                if cookie.name.startswith(".AspNetCore.Antiforgery."):
                    if cookie.value:
                        self.headers = {"Cookie": cookie.name + "=" + cookie.value}
                    else:
                        print("No cookie")
                    break

            if not self.current_token:
                soup = BeautifulSoup(response.text, "html.parser")
                token_input: Any = soup.find(
                    "input", {"name": "__RequestVerificationToken"}
                )
                if token_input:
                    self.current_token = token_input["value"]
        except Exception as e:
            print(f"Error refreshing token: {e}")

    def get_courses(self, departement: Departement):
        data = {
            "CritRech": "",
            "Module": departement,
            "Cycle": "",
            "TypeAff": "SigCrs",
            "__RequestVerificationToken": self.current_token,
        }
        response = self.session.post(self.url, headers=self.headers, data=data)
        return self.parse_courses_html(response.text, data)


    @staticmethod
    def parse_courses_html(html_content: str, data: Dict[str, str]) -> List[UQOCours]:
        print("Parsing HTML content to extract courses")
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the div containing course list
        courses_div: Any = soup.find("div", id="divLstCrs")
        if not courses_div:
            print("Could not find courses div in HTML")
            return []

        # Find all course items (each row contains a course)
        course_items = courses_div.find_all("div", class_="row")

        # Skip the header row
        course_items = [
            item for item in course_items if "row-entete" not in item.get("class", [])
        ]

        courses = []
        for item in course_items:
            # Extract sigle
            item: Any
            sigle_tag: Any = item.find("a")
            sigle = sigle_tag.text.strip() if sigle_tag else None

            # Extract titre
            titre_div = item.find_all(
                "div", class_="col-12 col-md-7 col-lg-5 order-3 order-lg-2"
            )
            titre = titre_div[0].text.strip() if titre_div else None

            # Extract cycle (from badge-warning span)
            cycle_span = item.find("span", class_="badge")
            cycle = cycle_span.text.strip()[:1] if cycle_span else None

            # Extract crédits
            credits_div = item.find_all(
                "div",
                class_="col-12 col-md-5 col-lg-1 text-left text-md-right text-xl-center text-xl-center order-4",
            )
            credit = credits_div[0].text.strip().split()[0] if credits_div else None

            # Extract préalables (empty in this example, but would be in the last column)
            prereq_div = item.find_all("div", class_="col-12 col-lg-3 order-5")
            prereq = []
            if prereq_div:
                prereq_links = prereq_div[0].find_all("a")
                prereq = [link.text.strip() for link in prereq_links]

            courses.append(
                UQOCours(**{
                    "sigle": sigle,
                    "titre": titre,
                    "cycle": cycle,
                    "credit": credit,
                    "préalable": prereq,
                })
            )

        return courses
    

