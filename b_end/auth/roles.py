from enum import Enum

class UserRole(str, Enum):
    VISITOR = "visitor"
    EDUCATOR = "educator"
    EXPERT = "expert"
    PERCEIVE_EXPERT = "perceive_expert"
    PERCEIVE_DEVELOPER = "perceive_developer"
    ADMIN = "admin"
