import os
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("TOKEN")
BASE_DIR = Path(__file__).parent
DEVELOPER_NAME = "Ahmed Bawazir"

LEVELS = [
    "المستوى الأول",
    "المستوى الثاني",
    "المستوى الثالث",
    "المستوى الرابع",
]

TERMS = ["الترم الأول", "الترم الثاني"]

SUBJECTS = [
    "Computer Skills",
    "Computer Programming",
    "Discrete Structures",
    "Differential Calculus",
    "Arabic Language",
    "English Language",
    "Culture Islamic",
]


def get_subject_folder(context, subject):
    level = context.user_data.get("level")
    term = context.user_data.get("term")

    new_folder = BASE_DIR / level / term / subject

    if level == "المستوى الأول" and term == "الترم الأول":
        if any(new_folder.glob("*.pdf")):
            return new_folder
        return BASE_DIR / subject

    return new_folder


def get_model_folder(context, subject):
    subject_folder = get_subject_folder(context, subject)
    return subject_folder / f"Models {subject}"


def make_keyboard(rows):
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [[level] for level in LEVELS]

    await update.message.reply_text(
        "📚 أهلاً بك في بوت طلاب التقنية - المستوى الأول\n\n"
        f"👨‍💻 المطوّر: {DEVELOPER_NAME}\n\n"
        "اختر مستواك الدراسي:",
        reply_markup=make_keyboard(keyboard),
    )


async def show_terms(update, context):
    keyboard = [[term] for term in TERMS]
    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        f"📚 {context.user_data['level']}\n\nاختر الترم:",
        reply_markup=make_keyboard(keyboard),
    )


async def show_main_menu(update, context):
    keyboard = [
        ["📚 الملازم"],
        ["📝 النماذج"],
        ["🔙 رجوع"],
    ]

    await update.message.reply_text(
        f"📚 {context.user_data['level']} - "
        f"{context.user_data['term']}\n\n"
        "اختر ما تريد:",
        reply_markup=make_keyboard(keyboard),
    )


async def show_subjects(update, context, page):
    context.user_data["page"] = page

    if page == "subjects":
        keyboard = [[subject] for subject in SUBJECTS]
        title = "📚 اختر المادة لتحميل الملازم:"
    else:
        keyboard = [
            [f"📝 {subject}"] for subject in SUBJECTS
        ]
        title = "📝 اختر المادة لعرض النماذج:"

    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        title,
        reply_markup=make_keyboard(keyboard),
    )


async def show_subject_files(update, context, subject):
    context.user_data["subject"] = subject
    context.user_data["page"] = "files"

    folder = get_subject_folder(context, subject)
    files = sorted(
        folder.glob("*.pdf"),
        key=lambda file: file.name.lower(),
    )

    if not files:
        await update.message.reply_text(
            f"📚 مادة {subject}\n\n"
            "🚧 لا توجد ملازم مضافة لهذه المادة حاليًا.",
            reply_markup=make_keyboard([["🔙 رجوع"]]),
        )
        return

    keyboard = [[f"📘 {file.stem}"] for file in files]
    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        f"📚 ملازم مادة {subject}:",
        reply_markup=make_keyboard(keyboard),
    )


async def show_model_types(update, context, subject):
    context.user_data["model_subject"] = subject
    context.user_data["page"] = "model_types"

    keyboard = [
        ["📅 نماذج شهرية"],
        ["📚 نماذج فصلية"],
        ["🔙 رجوع"],
    ]

    await update.message.reply_text(
        f"📝 نماذج مادة {subject}\n\nاختر نوع النماذج:",
        reply_markup=make_keyboard(keyboard),
    )


async def show_model_files(update, context, model_type):
    subject = context.user_data.get("model_subject")
    context.user_data["model_type"] = model_type
    context.user_data["page"] = "model_files"

    folder = get_model_folder(context, subject) / model_type
    files = sorted(
        folder.glob("*.pdf"),
        key=lambda file: file.name.lower(),
    )

    if not files:
        await update.message.reply_text(
            f"📝 {model_type}\n\n"
            "🚧 لا توجد نماذج مضافة حاليًا.",
            reply_markup=make_keyboard([["🔙 رجوع"]]),
        )
        return

    keyboard = [[f"📝 {file.stem}"] for file in files]
    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        f"📝 نماذج مادة {subject}:",
        reply_markup=make_keyboard(keyboard),
    )


async def send_selected_file(update, context, text):
    page = context.user_data.get("page")

    if page == "files":
        subject = context.user_data.get("subject")
        folder = get_subject_folder(context, subject)
        prefix = "📘 "
    elif page == "model_files":
        subject = context.user_data.get("model_subject")
        model_type = context.user_data.get("model_type")
        folder = get_model_folder(context, subject) / model_type
        prefix = "📝 "
    else:
        return False

    for file in folder.glob("*.pdf"):
        if text == f"{prefix}{file.stem}":
            await update.message.reply_document(
                document=file,
                caption=file.stem,
            )
            return True

    return False


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text
    page = context.user_data.get("page")

    if text == "🔙 رجوع":
        if page == "levels" or not page:
            await start(update, context)
        elif page == "terms":
            context.user_data.pop("level", None)
            await start(update, context)
        elif page == "main":
            await show_terms(update, context)
        elif page in ("subjects", "models"):
            await show_main_menu(update, context)
            context.user_data["page"] = "main"
        elif page == "files":
            await show_subjects(update, context, "subjects")
        elif page == "model_types":
            await show_subjects(update, context, "models")
        elif page == "model_files":
            await show_model_types(
                update,
                context,
                context.user_data["model_subject"],
            )
        return

    if text in LEVELS:
        context.user_data["level"] = text
        context.user_data["page"] = "terms"
        await show_terms(update, context)
        return

    if text in TERMS:
        context.user_data["term"] = text
        context.user_data["page"] = "main"
        await show_main_menu(update, context)
        return

    if page == "main":
        if text == "📚 الملازم":
            await show_subjects(update, context, "subjects")
            return

        if text == "📝 النماذج":
            await show_subjects(update, context, "models")
            return

    if page == "subjects" and text in SUBJECTS:
        await show_subject_files(update, context, text)
        return

    if page == "models" and text.startswith("📝 "):
        subject = text[3:]
        if subject in SUBJECTS:
            await show_model_types(update, context, subject)
            return

    if page == "model_types":
        if text == "📅 نماذج شهرية":
            await show_model_files(update, context, "نماذج شهرية")
            return

        if text == "📚 نماذج فصلية":
            await show_model_files(update, context, "نماذج فصليه")
            return

    if await send_selected_file(update, context, text):
        return

    await update.message.reply_text(
        "❓ اختر أحد الخيارات الموجودة في القائمة."
    )


def main():
    if not TOKEN:
        raise ValueError(
            "لم يتم العثور على TOKEN. تحقق من إعدادات التشغيل."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print("✅ البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
