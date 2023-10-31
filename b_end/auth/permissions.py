from .roles import UserRole
PERMISSIONS = {
    UserRole.VISITOR: {
        # "API": False,
        "web_portal": True,
        "Tools": False,
        "Services": True,
        "Dataset": False,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False,
    },
    UserRole.EDUCATOR: {
        # "API": False,
        "web_portal": True,
        "Tools": True,
        "Services": True,
        "Dataset": False,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.EXPERT: {
        # "API": False,
        "web_portal": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.PERCEIVE_EXPERT: {
        # "API": False,
        "web_portal": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.PERCEIVE_DEVELOPER: {
        # "API": True,
        "web_portal": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": True,
        "Change_User_Permissions": False
    },
    UserRole.ADMIN: {
        # "API": True,
        # dummy entries
        "web_portal": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": True,
        "Change_User_Permissions": True,
    },
}

