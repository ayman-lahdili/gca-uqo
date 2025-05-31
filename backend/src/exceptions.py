class CampagneNotFoundError(Exception):
    """Campagne not found"""

    def __init__(
        self,
        trimestre: int,
    ) -> None:
        super().__init__(f"Campagne introuvable pour le trimestre {trimestre}")


class CampagneTooAhead(Exception):
    """Campagne created too ahead of time"""


class ActiviteNotFoundError(Exception):
    """Activite not found"""


class CandidatureExistsError(Exception):
    """The candidature already exists"""


class NoStudentsFoundError(Exception):
    """Aucun étudiant n'a été trouvé"""


class StorageError(Exception):
    """Base exception for all storage-related errors."""


class FileSaveError(StorageError):
    """Raised when saving a file fails."""


class FileDeleteError(StorageError):
    """Raised when deleting a file fails."""


class FileReadError(StorageError):
    """Raised when reading a file fails."""


class ResumeNotFoundError(Exception):
    """Resume not found"""
