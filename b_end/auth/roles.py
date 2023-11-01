from enum import Enum, auto


class UserRole(str, Enum):
    VISITOR = "VISITOR"
    EDUCATOR = "EDUCATOR"
    EXPERT = "EXPERT"
    PERCEIVE_EXPERT = "PERCEIVE_EXPERT"
    PERCEIVE_DEVELOPER = "PERCEIVE_DEVELOPER"
    ADMIN = "ADMIN"

# class UserRole(Enum):
#     VISITOR = auto()
#     EDUCATOR = auto()
#     EXPERT = auto()
#     PERCEIVE_EXPERT = auto()
#     PERCEIVE_DEVELOPER = auto()
#     ADMIN = auto()
