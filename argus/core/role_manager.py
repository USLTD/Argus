class RoleManager:

    ADMIN = "Administrator"
    USER = "Standard User"

    current_role = ADMIN

    @classmethod
    def set_role(
            cls,
            role
    ):
        cls.current_role = role

    @classmethod
    def is_admin(cls):
        return (
            cls.current_role
            == cls.ADMIN
        )