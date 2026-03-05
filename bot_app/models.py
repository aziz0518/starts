from django.db import models

# 1. Kategoriya modeli
class Category(models.Model):
    # AutoField ogohlantirishini yo'qotish uchun id qo'shdik
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

# 2. Foydalanuvchilar modeli
class TelegramUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(unique=True, verbose_name="User ID")
    full_name = models.CharField(max_length=255, verbose_name="To'liq ismi")
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name="Username")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Bonus balans")
    
    referred_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="referals",
        verbose_name="Taklif qilgan shaxs"
    )
    
    is_blocked = models.BooleanField(default=False, verbose_name="Bloklanganmi?")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="A'zo bo'lgan vaqti")

    def __str__(self):
        return f"{self.full_name} ({self.user_id})"

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

# 3. Mahsulot modeli
class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Avvalgi xatoni oldini olish uchun null=True va blank=True qo'shildi
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products', 
        verbose_name="Kategoriyasi",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    price = models.PositiveIntegerField(verbose_name="Narxi (so'm)")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Rasmi")
    content = models.TextField(verbose_name="Mahsulot kodi/kaliti")
    is_sold = models.BooleanField(default=False, verbose_name="Sotildimi?")
    # created_at xatosini oldini olish uchun vaqtincha null=True
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

# 4. Buyurtmalar modeli
class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    # user xatosini oldini olish uchun null=True
    user = models.ForeignKey(
        TelegramUser, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name="Xaridor",
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        verbose_name="Mahsulot"
    )
    # amount xatosini oldini olish uchun default=0
    amount = models.PositiveIntegerField(default=0, verbose_name="To'langan summa")
    is_paid = models.BooleanField(default=False, verbose_name="To'lov holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sotib olingan vaqt")

    def __str__(self):
        name = self.user.full_name if self.user else "Noma'lum"
        return f"Order #{self.id} - {name}"

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

# 5. Savatcha modeli
class Cart(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

# 6. Promokod modeli
class PromoCode(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True, verbose_name="Kod")
    discount_percent = models.PositiveIntegerField(verbose_name="Chegirma %")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"