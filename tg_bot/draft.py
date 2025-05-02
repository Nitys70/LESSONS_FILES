async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_user(update)
    
    # Проверка авторизации
    if not await check_auth(update, context):
        user_message = update.message.text
        
        # Проверяем, не ввел ли пользователь пароль
        if user_message == AUTH_PASSWORD:
            context.user_data['authorized'] = True
            await update.message.reply_text(hello_message, parse_mode="HTML")
            # Инициализируем историю диалога после авторизации
            context.user_data['conversation_history'] = []
            return
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте еще раз.")
            return    
    
    # Основная логика обработки сообщений   
    user_message = update.message.text
    if user_message.lower().strip() == 'погода':
        return weather_handler.handle_weather_request(user_message)

    else:
    # Инициализируем историю, если её нет
        if 'conversation_history' not in context.user_data:
            context.user_data['conversation_history'] = []

        # Добавляем новое сообщение пользователя в историю
        context.user_data['conversation_history'].append({"role": "user", "content": user_message})

        try:
            # Формируем messages для OpenAI:
            # Начинаем с system-сообщения (необязательно, но помогает задать поведение бота)
            messages = [{"role": "system", "content": "Ты дружелюбный помощник."}]
            
            # Добавляем историю диалога
            messages.extend(context.user_data['conversation_history'])

            # Отправляем запрос к OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            reply = response.choices[0].message.content.strip()
            
            # Добавляем ответ ассистента в историю
            context.user_data['conversation_history'].append({"role": "assistant", "content": reply})

            # Ограничиваем длину истории, чтобы не превысить лимит токенов
            if len(context.user_data['conversation_history']) > MAX_HISTORY_LENGTH * 2:
                # Оставляем только последние MAX_HISTORY_LENGTH пар вопрос-ответ
                context.user_data['conversation_history'] = context.user_data['conversation_history'][-MAX_HISTORY_LENGTH*2:]

            await update.message.reply_text(reply)

        except Exception as e:
            print(f"OpenAI error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке вашего сообщения.")