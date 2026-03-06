import os, sys, django
from pathlib import Path
from asgiref.sync import sync_to_async
from django.utils import timezone

# --- DJANGO SETUP ---
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import LabeledPrice, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot_app.models import Product, Order, Category, TelegramUser, Cart, PromoCode
from django.conf import settings
# Faylning tepasiga buni qo'shing
import os
from aiogram import Bot, Dispatcher

bot = Bot(token=os.getenv('8446383314:AAFhDR8bvKs1DZSiDFA797xt0sE0Puoqg7Q'))
ADMIN_ID = 5013572418
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

storage = MemoryStorage()
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

class ShopStates(StatesGroup):
    search = State()
    waiting_ad = State()
    waiting_promo = State()

# --- DB FUNCTIONS ---
@sync_to_async
def register_user(user_id, name, username, ref_id=None):
    user, created = TelegramUser.objects.get_or_create(
        user_id=user_id,
        defaults={'full_name': name, 'username': username}
    )
    if created and ref_id and str(ref_id).isdigit() and int(ref_id) != user_id:
        referer = TelegramUser.objects.filter(user_id=ref_id).first()
        if referer:
            user.referred_by = referer
            user.save()
            referer.balance += 5000
            referer.save()
    return user

# --- KEYBOARDS ---
def get_main_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🛍 Do'kon", "🛒 Savatcha")
    kb.add("🔍 Qidiruv", "👤 Profil")
    kb.add("👫 Taklif qilish", "ℹ️ Yordam")
    if user_id == ADMIN_ID:
        kb.add("⚙️ Admin Panel")
    return kb

def get_admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📊 Statistika", "👥 Foydalanuvchilar")
    kb.add("📢 Reklama yuborish", "⬅️ Asosiy menyu")
    return kb

# --- HANDLERS ---

@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    ref_id = message.get_args() if message.get_args() else None
    await register_user(message.from_user.id, message.from_user.full_name, message.from_user.username, ref_id)
    await message.answer(f"👋 Assalomu alaykum, {message.from_user.full_name}!", reply_markup=get_main_kb(message.from_user.id))

# --- DO'KON ---
@dp.message_handler(lambda m: m.text == "🛍 Do'kon", state="*")
async def shop_menu(message: types.Message, state: FSMContext):
    await state.finish()
    cats = await sync_to_async(list)(Category.objects.all())
    if not cats: return await message.answer("📁 Hozircha kategoriyalar yo'q.")
    kb = InlineKeyboardMarkup(row_width=2)
    for c in cats: kb.insert(InlineKeyboardButton(c.name, callback_data=f"cat_{c.id}"))
    await message.answer("📁 Kategoriyani tanlang:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('cat_'), state="*")
async def cb_cat(c: types.CallbackQuery):
    prods = await sync_to_async(list)(Product.objects.filter(category_id=c.data.split('_')[1], is_sold=False))
    await bot.answer_callback_query(c.id)
    if not prods: return await bot.send_message(c.from_user.id, "❌ Mahsulot topilmadi.")
    for p in prods:
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🛒 Savatchaga qo'shish", callback_data=f"addcart_{p.id}"))
        await bot.send_message(c.from_user.id, f"📦 {p.name}\n💰 {p.price:,} so'm", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('addcart_'), state="*")
async def cb_add_cart(c: types.CallbackQuery):
    p_id = c.data.split('_')[1]
    user = await sync_to_async(TelegramUser.objects.get)(user_id=c.from_user.id)
    product = await sync_to_async(Product.objects.get)(id=p_id)
    await sync_to_async(Cart.objects.create)(user=user, product=product)
    await bot.answer_callback_query(c.id, text="Savatchaga qo'shildi! ✅")

# --- SAVATCHA ---
@dp.message_handler(lambda m: m.text == "🛒 Savatcha", state="*")
async def view_cart(message: types.Message, state: FSMContext):
    # state.finish() qilmaymiz, chunki discount o'chib ketadi
    user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    items = await sync_to_async(list)(Cart.objects.filter(user=user).select_related('product'))
    
    if not items:
        await state.finish()
        return await message.answer("🛒 Savatchangiz bo'sh.")

    data = await state.get_data()
    discount = data.get('discount', 0)
    
    total_price = sum(item.product.price for item in items)
    final_price = total_price * (100 - discount) // 100

    text = "<b>🛒 Savatchangiz:</b>\n\n"
    for i, item in enumerate(items, 1):
        text += f"{i}. {item.product.name} - {item.product.price:,} so'm\n"
    
    text += f"\n💰 Jami: <code>{total_price:,}</code> so'm"
    if discount > 0:
        text += f"\n🎁 Promokod: <code>-{discount}%</code>"
        text += f"\n✅ <b>To'lov uchun: <code>{final_price:,}</code> so'm</b>"
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💳 Sotib olish", callback_data="checkout_cart"),
        InlineKeyboardButton("🎟 Promokod kiritish", callback_data="apply_promo"),
        InlineKeyboardButton("🗑 Savatchani tozalash", callback_data="clear_cart")
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "apply_promo", state="*")
async def promo_start(c: types.CallbackQuery):
    await ShopStates.waiting_promo.set()
    await bot.send_message(c.from_user.id, "🎟 Promokodni yozing:")
    await c.answer()

@dp.message_handler(state=ShopStates.waiting_promo)
async def promo_check(message: types.Message, state: FSMContext):
    promo_code = message.text.strip()
    promo = await sync_to_async(PromoCode.objects.filter(code=promo_code, is_active=True).first)()
    
    if promo:
        await state.update_data(discount=promo.discount_percent)
        await message.answer(f"✅ Kod qabul qilindi! Chegirma: {promo.discount_percent}%")
    else:
        await message.answer("❌ Noto'g'ri yoki muddati o'tgan promokod.")
    
    # Savatchani yangilangan summa bilan ko'rsatamiz
    await view_cart(message, state)

@dp.callback_query_handler(lambda c: c.data == "checkout_cart", state="*")
async def cart_checkout(c: types.CallbackQuery, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=c.from_user.id)
    items = await sync_to_async(list)(Cart.objects.filter(user=user).select_related('product'))
    
    if not items:
        return await c.answer("Savatchangiz bo'sh!")

    data = await state.get_data()
    discount = data.get('discount', 0)
    
    total = sum(item.product.price for item in items)
    final = total * (100 - discount) // 100 # Haqiqiy ayrilayotgan joyi
    
    prices = [LabeledPrice(label=f"Savat ({len(items)} ta)", amount=int(final * 100))]
    
    await bot.send_invoice(
        c.from_user.id, 
        "🛍 Buyurtmalar to'lovi", 
        f"Jami {len(items)} ta mahsulot", 
        "cart_pay", 
        PAYMENT_TOKEN, 
        "UZS", 
        prices
    )
    await c.answer()

# --- QIDIRUV ---
@dp.message_handler(lambda m: m.text == "🔍 Qidiruv", state="*")
async def search_start(message: types.Message, state: FSMContext):
    await state.finish()
    await ShopStates.search.set()
    await message.answer("🔍 Mahsulot nomini yozing:", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=ShopStates.search)
async def search_process(message: types.Message, state: FSMContext):
    query = message.text
    prods = await sync_to_async(list)(Product.objects.filter(name__icontains=query, is_sold=False)[:10])
    await state.finish()
    if not prods:
        await message.answer("😔 Hech narsa topilmadi.", reply_markup=get_main_kb(message.from_user.id))
    else:
        for p in prods:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🛒 Savatga qo'shish", callback_data=f"addcart_{p.id}"))
            await message.answer(f"📦 {p.name}\n💰 {p.price:,} so'm", reply_markup=kb)
        await message.answer("✅ Natijalar ko'rsatildi.", reply_markup=get_main_kb(message.from_user.id))

# --- PROFIL ---
@dp.message_handler(lambda m: m.text == "👤 Profil", state="*")
async def profile_view(message: types.Message, state: FSMContext):
    await state.finish()
    user = await sync_to_async(TelegramUser.objects.filter(user_id=message.from_user.id).first)()
    orders_count = await sync_to_async(Order.objects.filter(user=user, is_paid=True).count)()
    text = (f"👤 <b>Profilingiz</b>\n\n🆔 ID: <code>{user.user_id}</code>\n"
            f"💰 Bonus: <code>{user.balance:,}</code> so'm\n🛍 Xaridlar: {orders_count} ta")
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_kb(message.from_user.id))

# --- ADMIN PANEL ---
@dp.message_handler(lambda m: m.text == "⚙️ Admin Panel", user_id=ADMIN_ID, state="*")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🛠 Admin Paneli", reply_markup=get_admin_kb())

async def show_users_page(message: types.Message, page: int = 1):
    page_size = 5
    offset = (page - 1) * page_size
    total = await sync_to_async(TelegramUser.objects.count)()
    users = await sync_to_async(list)(TelegramUser.objects.all().order_by('-joined_at')[offset:offset+page_size])
    
    text = f"<b>👥 Foydalanuvchilar ({total})</b>\n━━━━━━━━━━━━━━━\n"
    for i, u in enumerate(users, start=offset+1):
        text += f"{i}. {u.full_name}\n🆔 ID: <code>{u.user_id}</code>\n📅 {u.joined_at.strftime('%d.%m.%Y')}\n━━━━━\n"
    
    kb = InlineKeyboardMarkup(row_width=2)
    if page > 1: kb.insert(InlineKeyboardButton("⬅️", callback_data=f"upage_{page-1}"))
    if offset + page_size < total: kb.insert(InlineKeyboardButton("➡️", callback_data=f"upage_{page+1}"))
    
    if message.from_user.is_bot: await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else: await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "👥 Foydalanuvchilar", user_id=ADMIN_ID, state="*")
async def admin_users(message: types.Message, state: FSMContext):
    await state.finish()
    await show_users_page(message, 1)

@dp.callback_query_handler(lambda c: c.data.startswith('upage_'), user_id=ADMIN_ID, state="*")
async def cb_upage(c: types.CallbackQuery):
    await show_users_page(c.message, int(c.data.split('_')[1]))
    await c.answer()

@dp.message_handler(lambda m: m.text == "📊 Statistika", user_id=ADMIN_ID, state="*")
async def stats_view(message: types.Message, state: FSMContext):
    await state.finish()
    total_u = await sync_to_async(TelegramUser.objects.count)()
    total_o = await sync_to_async(Order.objects.filter(is_paid=True).count)()
    await message.answer(f"📊 <b>Statistika</b>\n\n👥 A'zolar: {total_u}\n💰 Sotuvlar: {total_o}", parse_mode="HTML")

# --- REKLAMA ---
@dp.message_handler(lambda m: m.text == "📢 Reklama yuborish", user_id=ADMIN_ID, state="*")
async def ad_start(message: types.Message, state: FSMContext):
    await state.finish()
    await ShopStates.waiting_ad.set()
    await message.answer("📢 Reklama xabarini yuboring:")

@dp.message_handler(state=ShopStates.waiting_ad, content_types=ContentType.ANY, user_id=ADMIN_ID)
async def ad_send(message: types.Message, state: FSMContext):
    users = await sync_to_async(list)(TelegramUser.objects.all())
    count = 0
    for u in users:
        try:
            await message.copy_to(u.user_id)
            count += 1
        except: pass
    await state.finish()
    await message.answer(f"✅ {count} kishiga yuborildi.", reply_markup=get_admin_kb())

# --- YORDAM VA ASOSIY ---
@dp.message_handler(lambda m: m.text == "ℹ️ Yordam", state="*")
async def help_h(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🆘 Savollar bo'yicha: @az1z_0518")

@dp.message_handler(lambda m: m.text == "⬅️ Asosiy menyu", state="*")
async def back_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🏠 Bosh sahifa", reply_markup=get_main_kb(message.from_user.id))

@dp.message_handler(lambda m: m.text == "👫 Taklif qilish", state="*")
async def invite(message: types.Message, state: FSMContext):
    await state.finish()
    bot_me = await bot.get_me()
    link = f"https://t.me/{bot_me.username}?start={message.from_user.id}"
    await message.answer(f"👫 Do'stlarni chaqiring va bonus oling!\n\nHavolangiz:\n{link}")

# --- TO'LOV MUVAFFAQIYATI ---
@dp.pre_checkout_query_handler(lambda q: True, state="*")
async def checkout_q(q: types.PreCheckoutQuery): await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT, state="*")
async def pay_success(message: types.Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    items = await sync_to_async(list)(Cart.objects.filter(user=user).select_related('product'))
    text = "✅ To'lov muvaffaqiyatli!\n\nKodlar:\n"
    for item in items:
        await sync_to_async(Order.objects.create)(user=user, product=item.product, amount=item.product.price, is_paid=True)
        text += f"🔹 {item.product.name}: <code>{item.product.content}</code>\n"
        item.product.is_sold = True
        await sync_to_async(item.product.save)()
    await sync_to_async(Cart.objects.filter(user=user).delete)()
    await state.finish() # To'lovdan keyin chegirma ma'lumotlarini tozalaymiz
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_kb(message.from_user.id))

@dp.callback_query_handler(lambda c: c.data == "clear_cart", state="*")
async def cb_clear(c: types.CallbackQuery, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=c.from_user.id)
    await sync_to_async(Cart.objects.filter(user=user).delete)()
    await state.finish()
    await bot.send_message(c.from_user.id, "🗑 Savatcha tozalandi.")
    await c.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)