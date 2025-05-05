import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import asyncio
from src.schemas.uqo import Departement, UQOCours
from src.cache import AsyncCache

class TokenManager:
    """Manages authentication tokens for UQO website.
    
    This class handles token retrieval and ensures tokens are refreshed
    when needed in a thread-safe manner.
    """
    
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._token: Optional[str] = None
        self._headers: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._last_refresh = 0
        self._refresh_interval = 1800  # 30 minutes in seconds
        
    async def get_token_and_headers(self) -> tuple[str, Dict[str, str]]:
        """Get the current token and headers, refreshing if necessary.
        
        Returns
        -------
        tuple[str, Dict[str, str]]
            The current token and headers needed for requests.
        """
        import time
        
        current_time = time.time()
        
        # Check if we need to refresh the token
        if (self._token is None or 
            current_time - self._last_refresh > self._refresh_interval):
            async with self._lock:
                # Check again in case another task refreshed while we were waiting
                if (self._token is None or 
                    current_time - self._last_refresh > self._refresh_interval):
                    await self._refresh_token()
                    self._last_refresh = time.time()
        
        assert self._token is not None, "Token should not be None after refresh"

        return self._token, self._headers
        
    async def _refresh_token(self) -> None:
        """Refresh the authentication token from the UQO website."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self._base_url)
                response.raise_for_status()
                
                # Extract token from cookies
                for cookie in client.cookies.jar:
                    if cookie.name.startswith(".AspNetCore.Antiforgery."):
                        if cookie.value:
                            self._headers = {"Cookie": f"{cookie.name}={cookie.value}"}
                        break
                
                # Extract token from HTML
                soup = BeautifulSoup(response.text, "html.parser")
                token_input: Any = soup.find("input", {"name": "__RequestVerificationToken"})
                
                assert token_input and "value" in token_input.attrs, "Token input not found"
                self._token = token_input["value"]
                    
        except (httpx.HTTPError, ValueError) as e:
            # Log the error but don't raise; we'll try again next time
            print(f"Error refreshing token: {str(e)}")
            # If we've never had a token, we need to raise
            if self._token is None:
                raise

class UQOCoursService:
    """Service for retrieving course information from UQO website."""
    
    def __init__(self, cours_cache: AsyncCache) -> None:  # Default 1 hour TTL
        """Initialize the UQO course service.
        
        Parameters
        ----------
        cache_ttl_seconds : int, optional
            Time-to-live for cache entries in seconds, by default 3600 (1 hour)
        """
        self.url = "https://etudier.uqo.ca/cours"
        self._token_manager = TokenManager(self.url)
        self._courses_cache = cours_cache

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
        # Use the cache with a creator function
        return await self._courses_cache.get_or_create(
            str(departement),  # Ensure the key is a string
            lambda: self._fetch_courses(departement)
        )
    
    async def _fetch_courses(self, departement: Departement) -> List[UQOCours]:
        """Fetch courses from the UQO website.
        
        This is the expensive operation that should be cached.
        
        Parameters
        ----------
        departement : Departement
            The department code to get courses for.
            
        Returns
        -------
        List[UQOCours]
            List of courses for the specified department.
        """
        try:
            # Get token and headers - this handles token refreshing internally
            token, headers = await self._token_manager.get_token_and_headers()
            
            # Prepare the form data
            data = {
                "CritRech": "",
                "Module": departement,
                "Cycle": "",
                "TypeAff": "SigCrs",
                "__RequestVerificationToken": token,
            }
            
            # Make the HTTP request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, headers=headers, data=data)
                response.raise_for_status()
                
                # Parse the response
                return self._parse_courses_html(response.text)
                
        except httpx.HTTPError as e:
            print(f"HTTP error fetching courses for {departement}: {str(e)}")
            raise
        except Exception as e:
            print(f"Error fetching courses for {departement}: {str(e)}")
            raise ValueError(f"Failed to fetch or parse courses: {str(e)}")
    
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
                UQOCours(**{
                    "sigle": sigle,
                    "titre": titre,
                    "cycle": cycle,
                    "credit": credit,
                    "préalable": prereq,
                })
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
            await self._courses_cache.invalidate(str(departement))
        else:
            await self._courses_cache.clear()