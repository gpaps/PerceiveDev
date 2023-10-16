from .roles import UserRole

PERMISSIONS = {
    UserRole.VISITOR: {
        # "API": False,
        "Tools": False,
        "Services": True,
        "Dataset": False,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.EDUCATOR: {
        # "API": False,
        "Tools": True,
        "Services": True,
        "Dataset": False,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.EXPERT: {
        # "API": False,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": False,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.PERCEIVE_EXPERT: {
        # "API": False,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": False,
        "Change_User_Permissions": False
    },
    UserRole.PERCEIVE_DEVELOPER: {
        # "API": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": True,
        "Change_User_Permissions": False
    },
    UserRole.ADMIN: {
        # "API": True,
        "Tools": True,
        "Services": True,
        "Dataset": True,
        "Trained_Models": True,
        "Code_Repo": True,
        "Change_User_Permissions": True
    },
}





# Mock permissions for each role
# ROLE_PERMISSIONS = {
#     Role.VISITOR: ["tools"],
#     Role.EDUCATOR: ["api", "tools"],
#     Role.EXPERT: ["api", "tools", "services"],
#     Role.PERCEIVE_EXPERT: ["api", "tools", "services", "datasets"],
#     Role.PERCEIVE_DEVELOPER: ["api", "tools", "services", "datasets", "code_repo"],
#     Role.ADMIN: ["api", "tools", "services", "datasets", "code_repo", "change_user_permissions"]
# }
