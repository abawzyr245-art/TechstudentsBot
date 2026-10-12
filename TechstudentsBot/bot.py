
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


def keyboard(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def get_subject_folder(context):
    return (
        BASE_DIR
        / context.user_data["level"]
        / context.user_data["term"]
        / context.user_data["subject"]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["page"] = "levels"

    await update.message.reply_text(
        "📚 أهلاً بك في بوت طلاب التقنية\n\n"
        f"👨‍💻 تطوير وبرمجة: {DEVELOPER_NAME}\n\n"
        "اختر مستواك الدراسي:",
        reply_markup=keyboard([[x] for x in LEVELS]),
    )


async def show_terms(update, context):
    context.user_data["page"] = "terms"
    await update.message.reply_text(
        f"📚 {context.user_data['level']}\nاختر الترم:",
        reply_markup=keyboard([[x] for x in TERMS] + [["🔙 رجوع"]]),
    )


async def show_menu(update, context):
    context.user_data["page"] = "main"
    await update.message.reply_text(
        "اختر ما تريد:",
        reply_markup=keyboard([
            ["📚 الملازم"],
            ["📝 النماذج"],
            ["🔙 رجوع"],
        ]),
    )


async def show_subjects(update, context, page):
    context.user_data["page"] = page

    if page == "subjects":
        rows = [[s] for s in SUBJECTS]
        title = "📚 اختر المادة:"
    else:
        rows = [[f"📝 {s}"] for s in SUBJECTS]
        title = "📝 اختر مادة النماذج:"

    await update.message.reply_text(
        title,
        reply_markup=keyboard(rows + [["🔙 رجوع"]]),
    )


async def show_files(update, context, folder, page, title):
    context.user_data["page"] = page

    files = sorted(
        folder.glob("*.pdf"),
        key=lambda f: f.name.lower(),
    ) if folder.exists() else []

    if not files:
        await update.message.reply_text(
            "🚧 لا توجد ملفات مضافة حاليًا.",
            reply_markup=keyboard([["🔙 رجوع"]]),
        )
        return

    context.user_data["files"] = {
        f.stem: str(f) for f in files
    }

    await update.message.reply_text(
        title,
        reply_markup=keyboard(
            [[f.stem] for f in files] + [["🔙 رجوع"]]
        ),
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text
    page = context.user_data.get("page")

    if text == "🔙 رجوع":
        if page == "terms":
            await start(update, context)
        elif page == "main":
            context.user_data.pop("term", None)
            await show_terms(update, context)
        elif page in ("subjects", "models"):
            await show_menu(update, context)
        elif page == "files":
            await show_subjects(update, context, "subjects")
        elif page == "model_subjects":
            await show_subjects(update, context, "models")
        elif page == "model_types":
            await show_subjects(update, context, "models")
        elif page == "model_files":
            context.user_data["page"] = "model_types"
            await show_model_types(update, context)
        else:
            await start(update, context)
        return

    if text in LEVELS:
        context.user_data["level"] = text
        await show_terms(update, context)
        return

    if text in TERMS:
        context.user_data["term"] = text
        await show_menu(update, context)
        return

    if page == "main":
        if text == "📚 الملازم":
            await show_subjects(update, context, "subjects")
        elif text == "📝 النماذج":
            await show_subjects(update, context, "models")
        return

    if page == "subjects" and text in SUBJECTS:
        context.user_data["subject"] = text
        folder = get_subject_folder(context) / "الملازم"
        await show_files(
            update, context, folder, "files",
            f"📚 ملازم {text}:",
        )
        return

    if page == "models" and text.startswith("📝 "):
        subject = text[3:]
        if subject in SUBJECTS:
            context.user_data["subject"] = subject
            await show_model_types(update, context)
        return

    if page == "model_types":
        if text == "📅 نماذج شهرية":
            folder = get_subject_folder(context) / "نماذج شهرية"
        elif text == "📚 نماذج فصلية":
            folder = get_subject_folder(context) / "نماذج فصلية"
        else:
            return

        await show_files(
            update, context, folder, "model_files",
            f"📝 نماذج {context.user_data['subject']}:",
        )
        return

    if page in ("files", "model_files"):
        file_path = context.user_data.get("files", {}).get(text)
        if file_path and Path(file_path).is_file():
            with open(file_path, "rb") as pdf:
                await update.message.reply_document(
                    document=pdf,
                    caption=Path(file_path).stem,
                )
            return

    await update.message.reply_text(
        "❓ اختر أحد الخيارات الموجودة في القائمة."
    )


async def show_model_types(update, context):
    context.user_data["page"] = "model_types"
    await update.message.reply_text(
        f"📝 نماذج مادة {context.user_data['subject']}\n"
        "اختر نوع النماذج:",
        reply_markup=keyboard([
            ["📅 نماذج شهرية"],
            ["📚 نماذج فصلية"],
            ["🔙 رجوع"],
        ]),
    )


def main():
    if not TOKEN:
        raise ValueError("تحقق من إعداد متغير TOKEN.")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
