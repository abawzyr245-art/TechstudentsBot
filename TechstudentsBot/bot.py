import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from pathlib import Path

TOKEN = os.getenv("TOKEN")

BASE_DIR = Path(__file__).parent

SUBJECTS = [
    "Computer Skills",
    "Computer Programming",
    "Discrete Structures",
    "Differential Calculus",
    "Arabic Language",
    "English Language",
    "Culture Islamic",
]

MODEL_FOLDERS = {
    "Computer Skills": BASE_DIR / "Computer Skills" / "Models Computer Skills",
    "Computer Programming": BASE_DIR / "Computer Programming" / "Models Computer Programming",
    "Discrete Structures": BASE_DIR / "Discrete Structures" / "Models Discrete Structures",
    "Differential Calculus": BASE_DIR / "Differential Calculus" / "Models Differential Calculus",
    "Arabic Language": BASE_DIR / "Arabic Language" / "Models Arabic Language",
    "English Language": BASE_DIR / "English Language" / "Models English Language",
    "Culture Islamic": BASE_DIR / "Culture Islamic" / "Models Culture Islamic",
}


async def show_main(update, context):
    keyboard = [
        ["📚 الملازم"],
        ["📝 النماذج"]
    ]

    await update.message.reply_text(
        "📚 أهلاً بك في بوت طلاب التقنية – المستوى الأول\n\n"
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await show_main(update, context)


async def malazem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page"] = "subjects"

    keyboard = [
        ["Computer Skills", "Computer Programming"],
        ["Discrete Structures", "Differential Calculus"],
        ["Arabic Language", "English Language"],
        ["Culture Islamic"],
        ["🔙 رجوع"]
    ]

    await update.message.reply_text(
        "📚 اختر المادة:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def show_subject(update, context, subject):
    context.user_data["page"] = "files"
    context.user_data["subject"] = subject

    subject_folder = BASE_DIR / subject

    files = sorted(
        [
            file for file in subject_folder.glob("*.pdf")
            if file.is_file()
        ],
        key=lambda file: file.name.lower()
    )

    if not files:
        await update.message.reply_text(
            f"📚 مادة {subject}\n\n"
            "🚧 لا توجد ملازم مضافة لهذه المادة حاليًا."
        )
        return

    keyboard = [
        [f"📘 {file.stem}"]
        for file in files
    ]

    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        f"📚 ملازم مادة {subject}:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def namathij(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page"] = "models"

    keyboard = [
        ["Models Computer Skills", "Models Computer Programming"],
        ["Models Discrete Structures", "Models Differential Calculus"],
        ["Models Arabic Language", "Models English Language"],
        ["Models Culture Islamic"],
        ["🔙 رجوع"]
    ]

    await update.message.reply_text(
        "📝 اختر المادة:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def show_models(update, context, subject):
    context.user_data["page"] = "model_types"
    context.user_data["model_subject"] = subject

    keyboard = [
        ["📅 نماذج شهرية"],
        ["📚 نماذج فصلية"],
        ["🔙 رجوع"]
    ]

    await update.message.reply_text(
        f"📝 نماذج مادة {subject}\n\n"
        "اختر نوع النماذج:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def show_model_files(update, context, subject, model_type):
    context.user_data["page"] = "model_files"
    context.user_data["model_subject"] = subject
    context.user_data["model_type"] = model_type

    model_folder = MODEL_FOLDERS[subject] / model_type

    files = sorted(
        [
            file for file in model_folder.glob("*.pdf")
            if file.is_file()
        ],
        key=lambda file: file.name.lower()
    )

    if not files:
        await update.message.reply_text(
            f"📝 {model_type}\n\n"
            "🚧 لا توجد نماذج مضافة حاليًا."
        )
        return

    keyboard = [
        [f"📝 {file.stem}"]
        for file in files
    ]

    keyboard.append(["🔙 رجوع"])

    await update.message.reply_text(
        f"📝 {model_type} - {subject}:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = context.user_data.get("page")

    if page == "files":
        await malazem(update, context)

    elif page == "model_types":
        await namathij(update, context)

    elif page == "model_files":
        subject = context.user_data.get("model_subject")

        if subject:
            await show_models(update, context, subject)
        else:
            await namathij(update, context)

    elif page in ("subjects", "models"):
        context.user_data.clear()
        await show_main(update, context)

    else:
        await show_main(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 الملازم":
        await malazem(update, context)
        return

    if text == "📝 النماذج":
        await namathij(update, context)
        return

    if text == "🔙 رجوع":
        await back(update, context)
        return

    if text in SUBJECTS:
        await show_subject(update, context, text)
        return

    model_subjects = {
        "Models Computer Skills": "Computer Skills",
        "Models Computer Programming": "Computer Programming",
        "Models Discrete Structures": "Discrete Structures",
        "Models Differential Calculus": "Differential Calculus",
        "Models Arabic Language": "Arabic Language",
        "Models English Language": "English Language",
        "Models Culture Islamic": "Culture Islamic"
    }

    if text in model_subjects:
        await show_models(
            update,
            context,
            model_subjects[text]
        )
        return

    if text in ["📅 نماذج شهرية", "📚 نماذج فصلية"]:
        subject = context.user_data.get("model_subject")

        if not subject:
            await namathij(update, context)
            return

        if text == "📅 نماذج شهرية":
            await show_model_files(
                update,
                context,
                subject,
                "نماذج شهرية"
            )
        else:
            await show_model_files(
                update,
                context,
                subject,
                "نماذج فصلية"
            )

        return

    subject = context.user_data.get("subject")

    if subject in SUBJECTS:
        subject_folder = BASE_DIR / subject

        files = sorted(
            [
                file for file in subject_folder.glob("*.pdf")
                if file.is_file()
            ],
            key=lambda file: file.name.lower()
        )

        for file in files:
            button_name = f"📘 {file.stem}"

            if text == button_name:
                if not file.exists():
                    await update.message.reply_text(
                        f"❌ الملف غير موجود:\n{file.name}"
                    )
                    return

                await update.message.reply_document(
                    document=file,
                    caption=f"📘 {file.stem}"
                )
                return

    model_subject = context.user_data.get("model_subject")
    model_type = context.user_data.get("model_type")

    if model_subject in MODEL_FOLDERS and model_type:
        model_folder = MODEL_FOLDERS[model_subject] / model_type

        files = sorted(
            [
                file for file in model_folder.glob("*.pdf")
                if file.is_file()
            ],
            key=lambda file: file.name.lower()
        )

        for file in files:
            button_name = f"📝 {file.stem}"

            if text == button_name:
                if not file.exists():
                    await update.message.reply_text(
                        f"❌ الملف غير موجود:\n{file.name}"
                    )
                    return

                await update.message.reply_document(
                    document=file,
                    caption=f"📝 {file.stem}"
                )
                return

    await update.message.reply_text(
        "❓ اختر أحد الخيارات الموجودة في القائمة."
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("✅ البوت يعمل الآن...")

    app.run_polling()


if __name__ == "__main__":
    main()
