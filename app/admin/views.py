from sqladmin.models import ModelView
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role]
    column_searchable_list = [User.email]
    column_filters = [StaticValuesFilter(
        column=User.role,
        values=[("user", "user"), ("admin", "admin")]
        )]
    page_size = 50
    can_delete = False

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price, Product.stock]
    column_searchable_list = [Product.name]
    column_filters = [
        OperationColumnFilter(Product.price),
        OperationColumnFilter(Product.stock)
    ]
    page_size = 50
    icon = "fa-solid fa-tag"

class CartAdmin(ModelView, model=Cart):
    column_list = [Cart.id, Cart.user_id, Cart.total_items]
    column_details_list = [Cart.id, Cart.user, Cart.total_items]
    column_filters = [
        OperationColumnFilter(Cart.total_items)
    ]
    page_size = 20
    icon = "fa-solid fa-shopping-cart"

class CartItemAdmin(ModelView, model=CartItem):
    column_list = [CartItem.id, CartItem.cart_id, CartItem.product_id, CartItem.quantity]
    column_searchable_list = [CartItem.cart_id]
    page_size = 50
    icon = "fa-solid fa-list-ul"

admin_views = [
    UserAdmin,
    ProductAdmin,
    CartAdmin,
    CartItemAdmin
]