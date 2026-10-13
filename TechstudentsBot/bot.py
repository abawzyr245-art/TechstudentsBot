import os
import logging
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

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

MONTHLY_FOLDER = "نماذج شهرية"
SEMESTER_FOLDER = "نماذج فصليه"


def keyboard(rows):
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
    )


def get_content_root():
    nested_folder = BASE_DIR / "TechstudentsBot"

    if any((nested_folder / level).is_dir() for level in LEVELS):
        return nested_folder

    return BASE_DIR


def get_term_folder(context):
    return (
        get_content_root()
        / context.user_data["level"]
        / context.user_data["term"]
    )


def get_subject_folder(context):
    return get_term_folder(context) / context.user_data["subject"]


def get_models_folder(context):
    subject_folder = get_subject_folder(context)
    models_folder = subject_folder / (
        f"Models {context.user_data['subject']}"
    )

    if models_folder.is_dir():
        return models_folder

    return subject_folder


def get_subject_names(context, models=False):
    term_folder = get_term_folder(context)

    if not term_folder.is_dir():
        return []

    subjects = []

    for folder in sorted(
        term_folder.iterdir(),
        key=lambda item: item.name.lower(),
    ):
        if not folder.is_dir():
            continue

        if folder.name.startswith("."):
            continue

        if models:
            models_folder = folder / f"Models {folder.name}"

            if not models_folder.is_dir():
                models_folder = folder

            has_monthly = (
                models_folder / MONTHLY_FOLDER
            ).is_dir()

            has_semester = (
                models_folder / SEMESTER_FOLDER
            ).is_dir()

            if not (has_monthly or has_semester):
                continue

        subjects.append(folder.name)

    return subjects


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["page"] = "levels"

    await update.message.reply_text(
        "📚 أهلاً بك في بوت طلاب التقنية\n\n"
        f"👨‍💻 تطوير وبرمجة: {DEVELOPER_NAME}\n\n"
        "اختر مستواك الدراسي:",
        reply_markup=keyboard([[level] for level in LEVELS]),
    )


async def show_terms(update, context):
    context.user_data["page"] = "terms"

    await update.message.reply_text(
        f"📚 {context.user_data['level']}\nاختر الترم:",
        reply_markup=keyboard(
            [[term] for term in TERMS] + [["🔙 رجوع"]]
        ),
    )


async def show_menu(update, context):
    context.user_data["page"] = "main"

    await update.message.reply_text(
        f"📚 {context.user_data['level']} - "
        f"{context.user_data['term']}\n\n"
        "اختر ما تريد:",
        reply_markup=keyboard([
            ["📚 الملازم"],
            ["📝 النماذج"],
            ["🔙 رجوع"],
        ]),
    )


async def show_subjects(update, context, page):
    context.user_data["page"] = page
    models = page == "models"
    subjects = get_subject_names(context, models=models)

    if not subjects:
        await update.message.reply_text(
            "🚧 لا توجد مواد مضافة في هذا الترم حاليًا.",
            reply_markup=keyboard([["🔙 رجوع"]]),
        )
        return

    if models:
        rows = [[f"📝 {subject}"] for subject in subjects]
        title = "📝 اختر مادة النماذج:"
    else:
        rows = [[subject] for subject in subjects]
        title = "📚 اختر المادة:"

    await update.message.reply_text(
        title,
        reply_markup=keyboard(rows + [["🔙 رجوع"]]),
    )


async def show_files(update, context, folder, page, title):
    context.user_data["page"] = page

    files = sorted(
        (
            file for file in folder.iterdir()
            if file.is_file() and file.suffix.lower() == ".pdf"
        ),
        key=lambda file: file.name.lower(),
    ) if folder.is_dir() else []

    context.user_data["files"] = {}

    if not files:
        await update.message.reply_text(
            "🚧 لا توجد ملفات PDF في هذا المجلد حاليًا.\n\n"
            f"📂 {folder.name}",
            reply_markup=keyboard([["🔙 رجوع"]]),
        )
        return

    file_buttons = []

    for index, file in enumerate(files):
        button_text = file.stem

        if button_text in context.user_data["files"]:
            button_text = f"{button_text} ({index + 1})"

        context.user_data["files"][button_text] = str(file)
        file_buttons.append([button_text])

    await update.message.reply_text(
        title,
        reply_markup=keyboard(
            file_buttons + [["🔙 رجوع"]]
        ),
    )


async def show_model_types(update, context):
    context.user_data["page"] = "model_types"

    models_folder = get_models_folder(context)
    rows = []

    if (models_folder / MONTHLY_FOLDER).is_dir():
        rows.append(["📅 نماذج شهرية"])

    if (models_folder / SEMESTER_FOLDER).is_dir():
        rows.append(["📚 نماذج فصلية"])

    if not rows:
        await update.message.reply_text(
            "🚧 لم تتم إضافة مجلدات النماذج لهذه المادة بعد.",
            reply_markup=keyboard([["🔙 رجوع"]]),
        )
        return

    await update.message.reply_text(
        f"📝 نماذج مادة {context.user_data['subject']}\n"
        "اختر نوع النماذج:",
        reply_markup=keyboard(rows + [["🔙 رجوع"]]),
    )


async def send_pdf(update, context, button_text):
    file_path = context.user_data.get("files", {}).get(button_text)

    if not file_path:
        return False

    path = Path(file_path)

    if not path.is_file():
        await update.message.reply_text(
            "⚠️ الملف غير موجود على الخادم. "
            "تحقق من رفعه إلى GitHub وإعادة نشر البوت."
        )
        return True

    try:
        with path.open("rb") as pdf:
            await update.message.reply_document(
                document=pdf,
                filename=path.name,
                caption=path.stem[:1024],
            )

        return True

    except (OSError, TelegramError):
        logger.exception("تعذر إرسال الملف: %s", path)

        await update.message.reply_text(
            "⚠️ تعذر إرسال الملف حاليًا. "
            "راجع سجل التشغيل في Railway لمعرفة السبب."
        )
        return True


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    page = context.user_data.get("page")

    if text == "🔙 رجوع":
        if page == "terms":
            await start(update, context)

        elif page == "main":
            await show_terms(update, context)

        elif page in ("subjects", "models"):
            await show_menu(update, context)

        elif page == "files":
            await show_subjects(update, context, "subjects")

        elif page == "model_types":
            await show_subjects(update, context, "models")

        elif page == "model_files":
            await show_model_types(update, context)

        else:
            await start(update, context)

        return

    if text in LEVELS:
        context.user_data["level"] = text
        context.user_data.pop("term", None)
        context.user_data.pop("subject", None)
        context.user_data.pop("files", None)
        await show_terms(update, context)
        return

    if text in TERMS and page == "terms":
        context.user_data["term"] = text
        context.user_data.pop("subject", None)
        context.user_data.pop("files", None)
        await show_menu(update, context)
        return

    if page == "main":
        if text == "📚 الملازم":
            await show_subjects(update, context, "subjects")

        elif text == "📝 النماذج":
            await show_subjects(update, context, "models")

        return

    if page == "subjects":
        if text in get_subject_names(context):
            context.user_data["subject"] = text
            subject_folder = get_subject_folder(context)

            notes_folder = subject_folder / "الملازم"

            if not notes_folder.is_dir():
                notes_folder = subject_folder

            await show_files(
                update,
                context,
                notes_folder,
                "files",
                f"📚 ملازم {text}:",
            )
        else:
            await update.message.reply_text(
                "❓ اختر مادة من القائمة الحالية."
            )
        return

    if page == "models":
        if text.startswith("📝 "):
            subject = text[3:]

            if subject in get_subject_names(context, models=True):
                context.user_data["subject"] = subject
                await show_model_types(update, context)
            else:
                await update.message.reply_text(
                    "❓ اختر مادة من القائمة الحالية."
                )
        return

    if page == "model_types":
        models_folder = get_models_folder(context)

        if text == "📅 نماذج شهرية":
            folder = models_folder / MONTHLY_FOLDER

        elif text == "📚 نماذج فصلية":
            folder = models_folder / SEMESTER_FOLDER

        else:
            return

        await show_files(
            update,
            context,
            folder,
            "model_files",
            f"📝 نماذج {context.user_data['subject']}:",
        )
        return

    if page in ("files", "model_files"):
        handled = await send_pdf(update, context, text)

        if handled:
            return

    await update.message.reply_text(
        "❓ اختر أحد الخيارات الموجودة في القائمة."
    )


def main():
    if not TOKEN:
        raise ValueError("تحقق من إعداد متغير TOKEN.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    logger.info("البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
