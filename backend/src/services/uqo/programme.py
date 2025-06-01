import json
import httpx
from httpx import AsyncClient, HTTPError
from structlog import BoundLogger
import re
from typing import List, Literal

from src.models.uqo import Departement, UQOProgramme
from src.cache import AsyncCache


class UQOAPIException(Exception):
    """Custom exception for UQO API related errors."""

    pass


class UQOProgrammeService:
    def __init__(
        self,
        *,
        programme_cache: AsyncCache[List[UQOProgramme]],
        http_client: AsyncClient,
        logger: BoundLogger,
    ) -> None:
        self.url = "https://etudier.uqo.ca/programmes"
        self._programme_cache = programme_cache
        self._http_client = http_client
        self._logger = logger

    async def get_programmes(
        self, departement: Departement, cycle: Literal["1", "2", "3"]
    ) -> List[UQOProgramme]:
        programmes_key = str(departement) + str(cycle)

        return await self._programme_cache.get_or_create(
            programmes_key, lambda: self._fetch_programmes(departement, cycle)
        )

    async def _fetch_programmes(
        self, departement: Departement, cycle: Literal["1", "2", "3"]
    ):
        pattern = re.compile(r"jsonLstRes\s*=\s*(\[.*)")

        try:
            resp = await self._http_client.get(self.url, timeout=30)
            resp.raise_for_status()
            html_text = resp.text
        except HTTPError as e:
            raise UQOAPIException(f"Failed to fetch {self.url}: {str(e)}")

        match = pattern.search(html_text)

        if match:
            json_string = match.group(1)[:-2]
            program_data = json.loads(json_string)
            result = [
                program
                for program in program_data
                if program["CdSectHtml"] == departement and program["CdCyc"] == cycle
            ]
            unique = dict((obj["CdPrgAdm"], obj) for obj in result).values()

            return [
                UQOProgramme(
                    **{
                        "sigle": c["CdPrgAdm"],
                        "label": c["CdPrgAdm"] + " - " + c["LblPrg"],
                    }
                )
                for c in unique
            ]
        else:
            raise UQOAPIException(
                "Could not find the pattern 'jsonLstRes = [...]' in the response text."
            )
