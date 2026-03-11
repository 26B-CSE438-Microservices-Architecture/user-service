from sqladmin import Admin, ModelView

from app.database import engine
from app.models.address import Address
from app.models.user import User


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.name,
        User.email,
        User.phone,
        User.role,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.name, User.email, User.phone]
    column_sortable_list = [User.created_at, User.email, User.phone]
    column_default_sort = [(User.created_at, True)]
    can_export = True


class AddressAdmin(ModelView, model=Address):
    name = "Address"
    name_plural = "Addresses"
    icon = "fa-solid fa-location-dot"

    column_list = [
        Address.id,
        Address.user_id,
        Address.address_title,
        Address.city,
        Address.district,
        Address.phone,
        Address.is_current,
        Address.created_at,
    ]
    column_searchable_list = [
        Address.address_title,
        Address.city,
        Address.district,
        Address.neighborhood,
        Address.phone,
    ]
    column_sortable_list = [Address.created_at, Address.city]
    column_default_sort = [(Address.created_at, True)]
    can_export = True


def setup_admin(app) -> None:
    admin = Admin(app, engine, base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(AddressAdmin)
