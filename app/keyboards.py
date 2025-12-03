from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from .loaders import get_courses


def categories_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["📚 الدورات الاحترافية", "🎓 المواد الجامعية"]], resize_keyboard=True
    )


def get_courses_keyboard(category: str) -> InlineKeyboardMarkup:
    courses = get_courses(category)
    buttons: List[List[InlineKeyboardButton]] = []
    for c in courses:
        buttons.append([
            InlineKeyboardButton(f"📖 {c.get('name', c.get('id'))}", callback_data=f"course_{c['id']}")
        ])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")])
    return InlineKeyboardMarkup(buttons)


def course_details_keyboard(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💳 Sham", callback_data=f"pay_sham_{course_id}"),
                InlineKeyboardButton("💳 HARAM", callback_data=f"pay_haram_{course_id}"),
            ],
            [InlineKeyboardButton("💬 تواصل مع المعلمة", callback_data="contact_admin")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="back_courses")],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu for students after login"""
    return ReplyKeyboardMarkup(
        [
            ["📚 الدورات الاحترافية", "🎓 المواد الجامعية"],
            ["💬 تواصل مع المعلمة", "📋 حالة الدفع"],
        ],
        resize_keyboard=True
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu for admin"""
    return ReplyKeyboardMarkup(
        [
            ["✅ الموافقة على الدفع", "👥 قائمة الطلاب"],
            ["📢  ارسال رسالة", "📊 الإحصائيات"],
            ["🏠 الرئيسية"],
        ],
        resize_keyboard=True
    )
