from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_product_keyboard(product_id, quantity=1):
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Miqdorni boshqarish tugmalari
    minus_btn = InlineKeyboardButton("➖", callback_data=f"minus_{product_id}_{quantity}")
    count_btn = InlineKeyboardButton(f"{quantity}", callback_data="count")
    plus_btn = InlineKeyboardButton("➕", callback_data=f"plus_{product_id}_{quantity}")
    
    # Savatga qo'shish va Savatga o'tish
    add_to_cart = InlineKeyboardButton("📥 Savatga qo'shish", callback_data=f"addcart_{product_id}_{quantity}")
    go_to_cart = InlineKeyboardButton("🛒 Savatni ko'rish", callback_data="view_cart")
    
    keyboard.row(minus_btn, count_btn, plus_btn)
    keyboard.add(add_to_cart)
    keyboard.add(go_to_cart)
    
    return keyboard