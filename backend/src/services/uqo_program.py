import json
import requests
import re
from typing import Any, Dict, List, Literal
from src.schemas.enums import Departement

class UQOAPIException(Exception):
    """Custom exception for UQO API related errors."""

    pass


class UQOProgramService:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug

    def get_programmes(
        self, departement: Departement, cycle: Literal["1", "2", "3"]
    ) -> List[Dict[str, Any]]:
        url = "https://etudier.uqo.ca/programmes"
        pattern = re.compile(r"jsonLstRes\s*=\s*(\[.*)")

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
                result = [
                    program
                    for program in program_data
                    if program["CdSectHtml"] == departement
                    and program["CdCyc"] == cycle
                ]
                unique = dict((obj["CdPrgAdm"], obj) for obj in result).values()

                return [
                    {"sigle": c["CdPrgAdm"], "label": c["CdPrgAdm"] + " - " + c["LblPrg"]}
                    for c in unique
                ]
            except json.JSONDecodeError as e:
                self.__debug_parse_error(json_string, e)
                raise UQOAPIException(f"JSON parsing error: {str(e)}")
        else:
            raise UQOAPIException(
                "Could not find the pattern 'jsonLstRes = [...]' in the response text."
            )

    @staticmethod
    def __debug_parse_error(json_string: str, error: json.JSONDecodeError):
        with open("debug/debug_json_string.json", "w", encoding="utf-8") as f:
            f.write(json_string)
        print(f"Successfully saved full string.")

        # Print context around the error position from the string
        error_pos = error.pos
        context_size = 60  # Show 60 chars before and after
        start_index = max(0, error_pos - context_size)
        end_index = min(len(json_string), error_pos + context_size)
        print("\n--- Problematic string context (from extracted string) ---")
        # Adding markers to pinpoint the exact error char
        print(
            f"...{json_string[start_index:error_pos]}<ERROR STARTS HERE>{json_string[error_pos:end_index]}..."
        )
        print("-" * (error_pos - start_index + len("...")) + "^ ERROR POS")
