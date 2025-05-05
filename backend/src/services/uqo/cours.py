import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import asyncio
from src.schemas.uqo import Departement, UQOCours
from src.cache import AsyncCache


class UQOCoursService:
    """Service for retrieving course information from UQO website.

    This implementation fetches a new token for each request and relies on
    the AsyncCache for concurrency handling to prevent duplicate requests.
    """

    def __init__(self, *, cours_cache: AsyncCache[List[UQOCours]]) -> None:
        """Initialize the UQO course service.

        Parameters
        ----------
        cours_cache : AsyncCache[List[UQOCours]]
            Cache for storing course data by department.
        """
        self.url = "https://etudier.uqo.ca/cours"
        self._cours_cache = cours_cache

    async def get_courses(self, departement: Departement) -> List[UQOCours]:
        """Get courses for a specific department.

        This method uses the cache to avoid redundant HTTP requests,
        and ensures only one HTTP request is made per department
        even with concurrent calls.

        Parameters
        ----------
        departement : Departement
            The department code to get courses for.

        Returns
        -------
        List[UQOCours]
            List of courses for the specified department.

        Raises
        ------
        httpx.HTTPError
            If there's an error communicating with the UQO website.
        ValueError
            If the response couldn't be parsed correctly.
        """
        # Convert department to string for use as cache key
        dept_key = str(departement)

        # Use the cache's get_or_create to handle concurrency and prevent dog-pile
        return await self._cours_cache.get_or_create(
            dept_key, lambda: self._fetch_courses(departement)
        )

    async def _fetch_courses(self, departement: Departement) -> List[UQOCours]:
        """Fetch courses from the UQO website.

        For each fetch, this method will:
        1. Get a fresh token and headers
        2. Make the request with the token
        3. Parse the results

        Parameters
        ----------
        departement : Departement
            The department code to get courses for.

        Returns
        -------
        List[UQOCours]
            List of courses for the specified department.

        Raises
        ------
        httpx.HTTPError
            If there's an error communicating with the UQO website.
        ValueError
            If the token couldn't be retrieved or response couldn't be parsed.
        """
        try:
            # Get a fresh token and headers for this specific request
            token, headers = await self._get_fresh_token()

            # Prepare the form data
            data = {
                "CritRech": "",
                "Module": departement,
                "Cycle": "",
                "TypeAff": "SigCrs",
                "__RequestVerificationToken": token,
            }

            # Make the request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, headers=headers, data=data)
                response.raise_for_status()

                # Parse and return the results
                return self._parse_courses_html(response.text)

        except httpx.HTTPError as e:
            print(f"HTTP error fetching courses for {departement}: {str(e)}")
            raise
        except Exception as e:
            print(f"Error fetching courses for {departement}: {str(e)}")
            raise ValueError(f"Failed to fetch or parse courses: {str(e)}")

    async def _get_fresh_token(self) -> tuple[str, Dict[str, str]]:
        """Get a fresh token and headers for making a request.

        For each new request, we need a fresh token from the UQO website.

        Returns
        -------
        tuple[str, Dict[str, str]]
            A tuple containing (token, headers) needed for making a request.

        Raises
        ------
        httpx.HTTPError
            If there's an error communicating with the UQO website.
        ValueError
            If the token couldn't be found in the response.
        """
        headers = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get the initial page to extract the token
            response = await client.get(self.url)
            response.raise_for_status()

            # Extract token from cookies
            for cookie in client.cookies.jar:
                if cookie.name.startswith(".AspNetCore.Antiforgery."):
                    if cookie.value:
                        headers = {"Cookie": f"{cookie.name}={cookie.value}"}
                    break

            # Extract token from HTML
            soup = BeautifulSoup(response.text, "html.parser")
            token_input: Any = soup.find(
                "input", {"name": "__RequestVerificationToken"}
            )

            assert token_input and "value" in token_input.attrs, (
                "Token not found in HTML"
            )
            token = token_input["value"]
            return token, headers

    def _parse_courses_html(self, html_content: str) -> List[UQOCours]:
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
                UQOCours(
                    **{
                        "sigle": sigle,
                        "titre": titre,
                        "cycle": cycle,
                        "credit": credit,
                        "préalable": prereq,
                    }
                )
            )

        return courses

    async def invalidate_cache(self, departement: Optional[Departement] = None) -> None:
        """Invalidate the cache for a specific department or all departments.

        Parameters
        ----------
        departement : Optional[Departement], optional
            The department to invalidate, or None to invalidate all, by default None
        """
        if departement is not None:
            await self._cours_cache.invalidate(str(departement))
        else:
            await self._cours_cache.clear()
