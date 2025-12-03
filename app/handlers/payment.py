from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime

from ..models import User, CourseEnrollment, Notification
from ..loaders import get_course_by_id


async def _find_or_create_user(tg_user_id: int) -> User:
    user = await User.find_one(User.telegram_id == tg_user_id)
    if not user:
        user = User(
            telegram_id=tg_user_id,
            full_name="",
            phone="",
            email="",
        )
        await user.save()
    return user


async def _notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    student: User,
    course_id: str,
    method: str,
    receipt_file_id: Optional[str] = None,
):
    admin_id = context.bot_data.get("ADMIN_ID")
    course = get_course_by_id(course_id) or {"name": course_id}
    if not admin_id:
        return
    caption = (
        f"طلب جديد لموافقة الدفع\n"
        f"الطالب: {student.full_name or student.telegram_id}\n"
        f"الدورة/المادة: {course.get('name')}\n"
        f"الطريقة: {'Sham' if method=='sham' else 'HARAM'}"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("موافقة", callback_data=f"admin_approve_{student.telegram_id}_{course_id}"),
            InlineKeyboardButton("رفض", callback_data=f"admin_reject_{student.telegram_id}_{course_id}"),
        ]
    ])
    try:
        if receipt_file_id:
            await context.bot.send_photo(chat_id=admin_id, photo=receipt_file_id, caption=caption, reply_markup=kb)
        else:
            await context.bot.send_message(chat_id=admin_id, text=caption, reply_markup=kb)
    except Exception:
        pass


async def pay_method_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data  # pay_sham_<course_id> or pay_haram_<course_id>
    parts = data.split("_")
    method = parts[1]  # sham or haram
    course_id = "_".join(parts[2:])

    course = get_course_by_id(course_id)
    if not course:
        await q.edit_message_text("لم يتم العثور على الدورة.")
        return

    context.user_data["payment_course_id"] = course_id
    context.user_data["payment_method"] = method

    sham = context.bot_data.get("SHAM") or ""
    haram = context.bot_data.get("HARAM") or ""
    method_label = "Sham" if method == "sham" else "HARAM"
    target_num = sham if method == "sham" else haram

    text = (
        f"طريقة الدفع: {method_label}\n"
        f"أرسل الآن صورة إثبات الدفع (screenshot/صورة للوصل).\n"
        f"رقم التحويل: {target_num}"
    )
    await q.edit_message_text(text)


async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
    course_id = context.user_data.get("payment_course_id")
    method = context.user_data.get("payment_method")
    mat_ids = context.user_data.get("payment_material_ids")
    if (not course_id and not mat_ids) or not method:
        # Not in payment flow
        return

    file_id = update.message.photo[-1].file_id
    student = await _find_or_create_user(update.effective_user.id)

    # Two flows: single course or multiple materials from university cart
    # mat_ids was already fetched above
    if mat_ids:
        for mid in mat_ids:
            updated = False
            for e in student.courses:
                if e.course_id == mid:
                    e.payment_method = method
                    e.payment_receipt = file_id
                    e.approval_status = "pending"
                    updated = True
                    break
            if not updated:
                student.courses.append(
                    CourseEnrollment(
                        course_id=mid,
                        payment_method=method,
                        payment_receipt=file_id,
                        approval_status="pending",
                    )
                )
    else:
        # single course/material
        updated = False
        for e in student.courses:
            if e.course_id == course_id:
                e.payment_method = method
                e.payment_receipt = file_id
                e.approval_status = "pending"
                updated = True
                break
        if not updated:
            student.courses.append(
                CourseEnrollment(
                    course_id=course_id,
                    payment_method=method,
                    payment_receipt=file_id,
                    approval_status="pending",
                )
            )
    student.notifications.append(
        Notification(
            student_id=student.telegram_id,
            type="payment_submitted",
            message=f"تم إرسال إثبات الدفع",
        )
    )
    student.last_active = datetime.utcnow()
    await student.save()

    # notify admin per item without sending the photo
    if mat_ids:
        for mid in mat_ids:
            await _notify_admin(context, student, mid, method, file_id)
    else:
        await _notify_admin(context, student, course_id, method, file_id)

    # Confirmation message to student
    await update.message.reply_text(
        "✅ **تم استلام إثبات الدفع**\n\n"
        "سيتم مراجعة طلبك من قبل المعلمة شهد طراف.\n"
        "سيتم إشعارك بحالة الموافقة قريباً."
    )
    # clear state
    context.user_data.pop("payment_course_id", None)
    context.user_data.pop("payment_material_ids", None)
    context.user_data.pop("payment_method", None)



def get_handlers():
    return [
        CallbackQueryHandler(pay_method_cb, pattern="^pay_(sham|haram)_"),
        MessageHandler(filters.PHOTO, receive_receipt),
    ]
