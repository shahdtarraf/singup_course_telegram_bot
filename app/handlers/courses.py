from typing import Optional, List, Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters

from ..models import User
from ..loaders import get_courses, get_course_by_id, get_group_link
from ..catalog import MATERIALS_BY_YEAR, MATERIALS, get_materials_by_year_semester, calculate_materials_price
from ..keyboards import get_courses_keyboard, course_details_keyboard, categories_keyboard


CATEGORY_PRO = "📚 الدورات الاحترافية"
CATEGORY_UNI = "🎓 المواد الجامعية"


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "📚 اختر نوع المحتوى:", 
            reply_markup=categories_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📚 اختر نوع المحتوى:", 
            reply_markup=categories_keyboard()
        )


def _category_from_text(text: str) -> Optional[str]:
    if text == CATEGORY_PRO:
        return "professional"
    if text == CATEGORY_UNI:
        return "university"
    return None


async def handle_category_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    # Handle main menu buttons
    if text == "🏠 الرئيسية":
        from .registration import start
        await start(update, context)
        return
    
    if text == "💬 تواصل مع المعلمة":
        context.user_data["awaiting_contact_message"] = True
        await update.message.reply_text(
            "💬 تواصل مع المعلمة\n\n"
            "أرسل رسالتك الآن وسيتم إيصالها للمعلمة شهد طراف.\n"
            "أرسل /cancel للإلغاء."
        )
        return
    
    if text == "📋 حالة الدفع":
        user_doc: User = await User.find_one(User.telegram_id == update.effective_user.id)
        if not user_doc or not user_doc.courses:
            await update.message.reply_text(
                "📋 حالة دفعاتك:\n\n"
                "❌ لم تقم بتسجيل أي دورات حتى الآن.\n\n"
                "اختر دورة أو مادة من القائمة الرئيسية وقم بالدفع."
            )
            return
        
        status_text = "📋 حالة دفعاتك:\n\n"
        for course in user_doc.courses:
            course_obj = get_course_by_id(course.course_id)
            course_name = course_obj.get("name") if course_obj else course.course_id
            status_emoji = "✅" if course.approval_status == "approved" else "⏳" if course.approval_status == "pending" else "❌"
            status_text += f"{status_emoji} {course_name}\n"
            status_text += f"   الحالة: {course.approval_status}\n\n"
        
        await update.message.reply_text(status_text)
        return
    
    category = _category_from_text(text)
    if not category:
        return
    context.user_data["last_category"] = category
    if category == "university":
        await _send_university_years(update, context)
    else:
        await update.message.reply_text("📚 اختر الدورة:", reply_markup=get_courses_keyboard(category))


async def back_courses_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    category = context.user_data.get("last_category") or "professional"
    if category == "university":
        await _edit_university_years(update, context)
    else:
        await update.callback_query.edit_message_text(
            "اختر الدورة/المادة:", reply_markup=get_courses_keyboard(category)
        )


async def course_details_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data  # course_<id>
    course_id = data.split("course_", 1)[1]
    course = get_course_by_id(course_id)
    if not course:
        await q.edit_message_text("❌ لم يتم العثور على الدورة.")
        return

    # Check enrollment status
    user_doc: User = await User.find_one(User.telegram_id == q.from_user.id)
    status = None
    if user_doc:
        for e in user_doc.courses:
            if e.course_id == course_id:
                status = e.approval_status
                break

    if status == "approved":
        # Show full details for approved students
        text = course.get("description") or f"الدورة: {course.get('name')}"
        group_link = get_group_link(course_id)
        if group_link:
            text += f"\n\n🔗 رابط المجموعة:\n{group_link}"
        text += "\n\n✅ أنت مسجل في هذه الدورة!"
        await q.edit_message_text(text)
        return

    # Not approved yet -> show full description + pay options
    text = course.get("description") or f"الدورة: {course.get('name')}"
    context.user_data["last_category"] = context.user_data.get("last_category") or "professional"
    await q.edit_message_text(text, reply_markup=course_details_keyboard(course_id))


# ================= University hierarchical UI =================
async def _send_university_years(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("📚 السنة الثالثة", callback_data="uni_year_3")],
        [InlineKeyboardButton("📚 السنة الرابعة (ذكاء)", callback_data="uni_year_4")],
        [InlineKeyboardButton("📚 السنة الخامسة (ذكاء)", callback_data="uni_year_5")],
    ]
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")])
    return await update.message.reply_text("🎓 المواد الجامعية\n\nاختر السنة:", reply_markup=InlineKeyboardMarkup(buttons))


async def _edit_university_years(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("📚 السنة الثالثة", callback_data="uni_year_3")],
        [InlineKeyboardButton("📚 السنة الرابعة (ذكاء)", callback_data="uni_year_4")],
        [InlineKeyboardButton("📚 السنة الخامسة (ذكاء)", callback_data="uni_year_5")],
    ]
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")])
    await update.callback_query.edit_message_text("🎓 المواد الجامعية\n\nاختر السنة:", reply_markup=InlineKeyboardMarkup(buttons))


async def uni_year_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    year = int(q.data.split("_")[-1])
    context.user_data["uni_ctx"] = {"year": year}
    year_name = {3: "الثالثة ", 4: "الرابعة (ذكاء)", 5: " (ذكاء)الخامسة"}.get(year, str(year))
    buttons = [
        [InlineKeyboardButton("📚 الفصل الأول", callback_data=f"uni_sem_{year}_1")],
        [InlineKeyboardButton("📚 الفصل الثاني", callback_data=f"uni_sem_{year}_2")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")],
    ]
    await q.edit_message_text(f"📖 السنة {year_name}\n\nاختر الفصل:", reply_markup=InlineKeyboardMarkup(buttons))


def _materials_keyboard(year: int, sem: int, selected: List[str]) -> InlineKeyboardMarkup:
    mats = get_materials_by_year_semester(year, sem)
    rows: List[List[InlineKeyboardButton]] = []
    for m in mats:
        mid = m["id"]
        name = m["name"]
        chosen = "✅" if mid in selected else "➕"
        rows.append([
            InlineKeyboardButton(f"📖 {name}", callback_data=f"uni_detail_{mid}"),
            InlineKeyboardButton(f"{chosen}", callback_data=f"uni_toggle_{mid}"),
        ])
    # cart and back
    rows.append([InlineKeyboardButton(f"🧺 السلة ({len(selected)})", callback_data="uni_cart")])
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")])
    return InlineKeyboardMarkup(rows)


async def uni_sem_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, _, year, sem = q.data.split("_")
    year, sem = int(year), int(sem)
    context.user_data["uni_ctx"] = {"year": year, "sem": sem}
    selected: List[str] = context.user_data.get("uni_selected") or []
    await q.edit_message_text(
        "اختر المواد (يمكنك اختيار أكثر من مادة):",
        reply_markup=_materials_keyboard(year, sem, selected),
    )


async def uni_detail_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mid = q.data.split("uni_detail_", 1)[1]
    mat: Dict = MATERIALS.get(mid) or {"id": mid, "name": mid}
    # Professional details text
    text = (
        f"📚 {mat.get('name')}\n\n"
        f"👨‍🏫 المدربة: {mat.get('instructor', '-')}\n"
        f"📅 السنة/الفصل: السنة {mat.get('year', '-')} / الفصل {mat.get('semester', '-')}\n"
        f"💰 السعر: 75,000 ل.س\n"
        f"🎁 خصم: عند اختيار مادتين → 50,000 ل.س لكل مادة\n\n"
        f"📖 الوصف:\n{mat.get('description', 'وصف المادة')}\n\n"
        f"📝 محتوى برنامج التدريب:\n"
        f"• ملخصات منظمة وشاملة\n"
        f"• اختبارات قصيرة بعد كل محاضرة\n"
        f"• تدريب عملي على أسئلة دورات سابقة\n"
        f"• تقييم دوري لمستوى التقدم الأكاديمي"
    )
    # Add payment and contact buttons
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 الدفع عبر Sham", callback_data=f"pay_sham_{mid}"), InlineKeyboardButton("💳 الدفع عبر HARAM", callback_data=f"pay_haram_{mid}")],
        [InlineKeyboardButton("➕ إضافة للسلة", callback_data=f"uni_toggle_{mid}" )],
        [InlineKeyboardButton("💬 تواصل مع الإدارة", callback_data="contact_admin")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"uni_sem_{mat.get('year')}_{mat.get('semester')}")],
    ])
    await q.edit_message_text(text, reply_markup=kb)


async def uni_toggle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mid = q.data.split("uni_toggle_", 1)[1]
    selected: List[str] = context.user_data.get("uni_selected") or []
    if mid in selected:
        selected.remove(mid)
        msg = "❌ تم إزالة المادة من السلة"
    else:
        selected.append(mid)
        # Show discount notification
        if len(selected) == 2:
            msg = "✅ تم إضافة المادة! 🎁 خصم 25% تم تطبيقه على المادتين"
        else:
            msg = "✅ تم إضافة المادة للسلة"
    context.user_data["uni_selected"] = selected
    await q.answer(msg, show_alert=False)
    ctx = context.user_data.get("uni_ctx") or {}
    year, sem = ctx.get("year"), ctx.get("sem")
    if year and sem:
        await q.edit_message_text(
            f"اختر المواد (محدد: {len(selected)}):",
            reply_markup=_materials_keyboard(year, sem, selected),
        )
    else:
        await _edit_university_years(update, context)


def _calc_price(selected: List[str]) -> int:
    return calculate_materials_price(selected)


async def uni_cart_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    selected: List[str] = context.user_data.get("uni_selected") or []
    if not selected:
        await q.edit_message_text("❌ سلتك فارغة. اختر مواداً أولاً.")
        return
    names = [MATERIALS.get(mid, {"name": mid}).get("name", mid) for mid in selected]
    total = _calc_price(selected)
    discount_note = ""
    if len(selected) == 1:
        discount_note = "\n\n💰 السعر الحالي: 75,000 ل.س"
    elif len(selected) == 2:
        discount_note = "\n\n🎁 تم تطبيق خصم 2 مواد!\n💰 السعر الحالي: 50,000 ل.س × 2 = 100,000 ل.س"
    else:
        discount_note = f"\n\n🎁 خصم متعدد!\n💰 السعر الحالي: 50,000 ل.س × {len(selected)}"
    
    text = (
        f"🧺 سلتك الحالية:\n\n"
        + "\n".join([f"✓ {n}" for n in names])
        + f"\n\n📊 الملخص:\n"
        f"عدد المواد: {len(selected)}"
        f"{discount_note}\n\n"
        f"💵 الإجمالي النهائي: {total:,} ل.س"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 الدفع عبر Sham", callback_data="uni_pay_sham"), InlineKeyboardButton("💳 الدفع عبر HARAM", callback_data="uni_pay_haram")],
        [InlineKeyboardButton("⬅️ رجوع للمواد", callback_data=f"uni_sem_{context.user_data.get('uni_ctx',{}).get('year',3)}_{context.user_data.get('uni_ctx',{}).get('sem',1)}")],
        [InlineKeyboardButton("🗑️ إلغاء السلة", callback_data="uni_clear")],
    ])
    await q.edit_message_text(text, reply_markup=kb)


async def uni_clear_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.pop("uni_selected", None)
    ctx = context.user_data.get("uni_ctx") or {}
    year, sem = ctx.get("year"), ctx.get("sem")
    if year and sem:
        await q.edit_message_text("تم إفراغ السلة.", reply_markup=_materials_keyboard(year, sem, []))
    else:
        await _edit_university_years(update, context)


async def uni_pay_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    selected: List[str] = context.user_data.get("uni_selected") or []
    if not selected:
        await q.edit_message_text("سلتك فارغة.")
        return
    method = "sham" if q.data.endswith("sham") else "haram"
    context.user_data["payment_material_ids"] = selected.copy()
    context.user_data["payment_method"] = method
    sham = context.bot_data.get("SHAM") or ""
    haram = context.bot_data.get("HARAM") or ""
    target_num = sham if method == "sham" else haram
    await q.edit_message_text(
        f"طريقة الدفع: {'Sham' if method=='sham' else 'HARAM'}\nأرسل الآن صورة إثبات الدفع.\nرقم التحويل: {target_num}"
    )


def get_handlers():
    return [
        CommandHandler("courses", show_categories),
        CommandHandler("university", show_categories),
        # Main menu buttons - must be before other text handlers
        MessageHandler(filters.TEXT & filters.Regex("^(📚 الدورات الاحترافية|🎓 المواد الجامعية|💬 تواصل مع المعلمة|📋 حالة الدفع|🏠 الرئيسية)$"), handle_category_text),
        CallbackQueryHandler(back_courses_cb, pattern="^back_courses$"),
        CallbackQueryHandler(course_details_cb, pattern="^course_"),
        # University hierarchy
        CallbackQueryHandler(uni_year_cb, pattern="^uni_year_"),
        CallbackQueryHandler(uni_sem_cb, pattern="^uni_sem_\\d+_\\d+$"),
        CallbackQueryHandler(uni_detail_cb, pattern="^uni_detail_"),
        CallbackQueryHandler(uni_toggle_cb, pattern="^uni_toggle_"),
        CallbackQueryHandler(uni_cart_cb, pattern="^uni_cart$"),
        CallbackQueryHandler(uni_clear_cb, pattern="^uni_clear$"),
        CallbackQueryHandler(uni_pay_cb, pattern="^uni_pay_(sham|haram)$"),
        CallbackQueryHandler(contact_admin_cb, pattern="^contact_admin$"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_student_contact_message, block=False),
    ]


async def contact_admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact admin button from course details"""
    q = update.callback_query
    await q.answer()
    context.user_data["awaiting_contact_message"] = True
    await q.edit_message_text(
        "💬 تواصل مع المعلمة\n\n"
        "أرسل رسالتك الآن وسيتم إيصالها للمعلمة شهد طراف.\n"
        "أرسل /cancel للإلغاء."
    )


async def handle_student_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle student messages when contacting admin"""
    if not update.message or not update.message.text:
        return
    
    # Check if student is waiting to send a contact message
    if context.user_data.get("awaiting_contact_message"):
        admin_id = context.bot_data.get("ADMIN_ID")
        student_name = update.effective_user.full_name or f"الطالب {update.effective_user.id}"
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📧 رسالة من الطالب\n\n"
                     f"👤 الاسم: {student_name}\n"
                     f"🆔 المعرف: {update.effective_user.id}\n\n"
                     f"💬 الرسالة:\n{update.message.text}",
            )
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
            return
        context.user_data.pop("awaiting_contact_message", None)
        await update.message.reply_text("✅ تم إرسال رسالتك للمعلمة شهد طراف بنجاح!")
        return
